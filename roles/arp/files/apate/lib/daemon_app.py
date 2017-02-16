# coding=utf-8
"""This module provides several classes that are used to implement a ARP spoofing daemon.

Classes:
    _DaemonApp: Abstract class, that should be inherited.
    HolisticDaemonApp: Inherits _DaemonApp and implements the holistist spoofing mode.
    SelectiveDaemonApp: Inherits _DaemonApp and implements the selective spoofing mode.
    DaemonError: Error that indicates the daemon's failure.

"""
import os
import logging
import time
import threading
import collections
import dns.resolver
import netifaces as ni
from netaddr import IPAddress, IPNetwork, AddrFormatError

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import conf, sendp, ARP, Ether, ETHER_BROADCAST, ICMPv6NDOptDstLLAddr, ICMPv6ND_NA, IPv6

import util
from sniff_thread import HolisticSniffThread, SelectiveSniffThread
from apate_redis import ApateRedis
from misc_thread import ARPDiscoveryThread, IGMPDiscoveryThread, PubSubThread, MulticastPingDiscoveryThread, MulticastListenerDiscoveryThread


class _DaemonApp(object):
    """This is an abstract class, which should be inherited to define the
    Apate daemon's behaviour."""

    def __init__(self, logger, interface, pidfile, stdout, stderr, dns_file):
        """Initialises several things needed to define the daemons behaviour.

        Args:
            logger (logging.Logger): Used for logging messages.
            interface (str): The network interface which should be used. (e.g. eth0)
            pidfile (str): Path of the pidfile, used by the daemon.
            stdout (str): Path of stdout, used by the daemon.
            stderr (str): Path of stderr, used by the daemon.
            dns_file (str): Path of file containing the nameservers.

        Raises:
            DaemonError: Signalises the failure of the daemon.
        """
        # disable scapys verbosity global
        conf.verb = 0

        self.stdin_path = os.devnull
        self.stdout_path = stdout
        self.stderr_path = stderr
        self.pidfile_path = pidfile
        self.pidfile_timeout = 5
        # self.pidfile_timeout = 0

        self.logger = logger
        self.interface = interface

        # namedtuple for providing information about the IP configuration
        IPInfo = collections.namedtuple('IPInfo', 'ip, netmask, network, gateway, mac, gate_mac, dns_servers, redis')

        if_info = None
        try:
            if_info = ni.ifaddresses(self.interface)
        except ValueError as e:
            self.logger.error("An error concerning the interface {} has occurred: {}".format(self.interface, str(e)))
            raise DaemonError()

        self.ipv4 = None
        self.ipv6 = None

        # get mac address of specified interface
        mac = if_info[ni.AF_LINK][0]['addr']
        rs = dns.resolver.Resolver(filename=dns_file)

        try:
            # get ip of specified interface
            ip = if_info[ni.AF_INET][0]['addr']
            # get subnetmask of specified interface
            netmask = if_info[ni.AF_INET][0]['netmask']
            # get the network address
            network = IPNetwork("{}/{}".format(ip, netmask))

            # get default gateway
            gateway = ni.gateways()["default"][ni.AF_INET][0]

            try:
                # get MAC address of gateway
                gate_mac = util.get_mac(gateway, self.interface)
                if not gate_mac:
                    raise DaemonError()
            except Exception:
                self.logger.error("Unable to get MAC address of IPv4 Gateway")
                # raise DaemonError()

            # get all ipv4 nameservers
            dns_servers = [x for x in rs.nameservers if IPAddress(x).version == 4]
            # store ipv4 information
            self.ipv4 = IPInfo(ip, netmask, network, gateway, mac, gate_mac, dns_servers, None)
        except AddrFormatError as afe:
            # this should never happen, because values are retrieved via netifaces library
            self.logger.error("A error happened during determinig the IPv4 network: {}".format(str(afe)))
            # raise DaemonError()
        except KeyError:
            self.logger.error("No IPv4 default gateway is configured")
            # raise DaemonError()

        try:
            # global IPv6 if self.ipv6 results in True
            # get ipv6 addresses of specified interface
            ip = [x for x in if_info[ni.AF_INET6] if not IPAddress(x['addr'].split("%")[0]).is_private()]
            #self.linklocal = [x['addr'].split("%")[0] for x in if_info[ni.AF_INET6] if IPAddress(x['addr'].split("%")[0]).is_link_local()][0]

            # get network address
            network = IPNetwork("{}/{}".format(ip[0]['addr'], ip[0]['netmask']))
            # get subnetmask of specified interface
            netmask = [entry['netmask'] for entry in if_info[ni.AF_INET6]]
            # get default gateway
            gateway = ni.gateways()["default"][ni.AF_INET6][0]

            try:
                # get MAC address of gateway
                gate_mac = util.get_mac6(gateway, self.interface)
                if not gate_mac:
                    raise DaemonError()
            except Exception:
                self.logger.error("Unable to get MAC address of IPv6 Gateway")
                # raise DaemonError()

            # get all ipv6 nameservers
            dns_servers = [x for x in rs.nameservers if IPAddress(x).version == 6]
            # store ipv6 information
            self.ipv6 = IPInfo(ip, netmask, network, gateway, mac, gate_mac, dns_servers, None)
        except AddrFormatError as afe:
            # this should never happen, because values are retrieved via netifaces library
            self.logger.error("A error happened during determinig the IPv6 network: {}".format(str(afe)))
            # raise DaemonError()
        except KeyError:
            self.logger.error("No IPv6 default gateway is configured")
            # raise DaemonError()

        # if not self.ipv4 and not self.ipv6:
        if not any((self.ipv4, self.ipv6)):
            # at least ipv4 or ipv6 has to be configured
            raise DaemonError()

    def _return_to_normal(self):
        """This method should be overriden to define the actions to be done when stopping the daemon."""
        pass

    def exit(self, signal_number, stack_frame):
        """This method is called if the daemon stops."""
        self._return_to_normal()
        raise SystemExit()

    def run(self):
        """This method should be overriden to define the daemon's behaviour."""
        pass


class HolisticDaemonApp(_DaemonApp):
    """Implements the abstract class _DaemonApp and also implements the holistic spoofing mode of Apate.
    The holistic spoofing mode requires less resources than the selective spoofing mode,
    e.g.: redis-server is not needed. This mode is suitable for small networks (e.g. /24).
    """

    __SLEEP = 20
    """int: Defines the time to sleep after packets are sent before they are sent anew."""

    def __init__(self, logger, interface, pidfile, stdout, stderr, dns_file):
        """Initialises several things needed to define the daemons behaviour.

        Args:
            logger (logging.Logger): Used for logging messages.
            interface (str): The network interface which should be used. (e.g. eth0)
            pidfile (str): Path of the pidfile, used by the daemon.
            stdout (str): Path of stdout, used by the daemon.
            stderr (str): Path of stderr, used by the daemon.
            dns_file (str): Path of file containing the nameservers.

        Raises:
            DaemonError: Signalises the failure of the daemon.
        """
        super(self.__class__, self).__init__(logger, interface, pidfile, stdout, stderr, dns_file)

        self.sniffthread = HolisticSniffThread(self.interface, self.ipv4, self.ipv6)
        self.sniffthread.daemon = True

    def _return_to_normal(self):
        """This method is called when the daemon is stopping.
        First, sends a GARP broadcast request to all clients to tell them the real gateway.
        Then an ARP request is sent to every client, so that they answer the real gateway and update its ARP cache.
        """
        # clients gratutious arp
        sendp(
            Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.ipv4.gateway, pdst=self.ipv4.gateway, hwdst=ETHER_BROADCAST,
                                             hwsrc=self.ipv4.gate_mac))
        # to clients so that they send and arp reply to the gateway
        # sendp(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=str(self.network), hwsrc=self.gate_mac))

    def exit(self, signal_number, stack_frame):
        """This method is called from the python-daemon when the daemon is stopping.
        Threads are stopped and clients are despoofed via _return_to_normal().
        """
        self._return_to_normal()
        raise SystemExit()

    def run(self):
        """Starts the thread, which is sniffing incoming ARP packets and sends out packets to spoof
        all clients on the network and the gateway. This packets are sent every __SLEEP seconds.

        Note:
            First, a ARP request packet is generated for every possible client of the network.
            This packets are directed at the gateway and update existing entries of the gateway's ARP table.
            So the gateway is not flooded with entries for non-existing clients.

            Second, a GARP broadcast request packet is generated to spoof every client on the network.
        """
        # start sniffing thread
        self.sniffthread.start()

        # generates a packet for each possible client of the network
        # these packets update existing entries in the arp table of the gateway
        # packets = [Ether(dst=self.gate_mac) / ARP(op=1, psrc=str(x), pdst=str(x)) for x in self.ip_range]

        # gratuitous arp to clients
        # updates the gateway entry of the clients arp table
        packets = [Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.ipv4.gateway, pdst=self.ipv4.gateway, hwdst=ETHER_BROADCAST)]
        while True:
            sendp(packets)
            time.sleep(self.__SLEEP)


class SelectiveDaemonApp(_DaemonApp):
    """Implements the abstract class _DaemonApp and also implements the selective spoofing mode of Apate.
    The selective spoofing mode requires more resources than the holistic spoofing mode,
    e.g.: the redis-server. This mode only generates packets for existing clients (not every possible client).
    This mode is suitable for bigger networks, as the bottleneck of this mode is virtually only the host discovery.
    """

    __SLEEP = 4
    """int: Defines the time to sleep after packets are sent before they are sent anew."""

    def __init__(self, logger, interface, pidfile, stdout, stderr, dns_file):
        """Initialises several things needed to define the daemons behaviour.

        Args:
            logger (logging.Logger): Used for logging messages.
            interface (str): The network interface which should be used. (e.g. eth0)
            pidfile (str): Path of the pidfile, used by the daemon.
            stdout (str): Path of stdout, used by the daemon.
            stderr (str): Path of stderr, used by the daemon.
            dns_file (str): Path of file containing the nameservers.

        Raises:
            DaemonError: Signalises the failure of the daemon.
        """
        super(self.__class__, self).__init__(logger, interface, pidfile, stdout, stderr, dns_file)

        # add redis objects to the ip tuples
        self.ipv4 = self.ipv4._replace(redis=ApateRedis(str(self.ipv4.network.network), logger))
        self.ipv6 = self.ipv6._replace(redis=ApateRedis(str(self.ipv6.network.network), logger))

        # used for thread synchronisation (for waking this thread)
        self.sleeper = threading.Condition()

        self.threads = {}
        # Initialise threads
        self.threads['sniffthread'] = SelectiveSniffThread(self.interface, self.ipv4, self.ipv6, self.sleeper)
        self.threads['psthread'] = PubSubThread(self.ipv4.redis, self.logger)
        self.threads['arpthread'] = ARPDiscoveryThread(self.ipv4.gateway, str(self.ipv4.network.network))
        self.threads['igmpthread'] = IGMPDiscoveryThread(self.ipv4)
        self.threads['icmpv6thread'] = MulticastPingDiscoveryThread()
        self.threads['mldv2thread'] = MulticastListenerDiscoveryThread()
        self.threads['psthread6'] = PubSubThread(self.ipv6.redis, self.logger)

        # declare all threads as deamons
        for worker in self.threads:
            self.threads[worker].daemon = True

    def _return_to_normal(self):
        """This method is called when the daemon is stopping.
        First, sends a GARP broadcast request to all clients to tell them the real gateway.
        Then ARP replies for existing clients are sent to the gateway.
        If IPv6 is enabled, Apate tells the clients the real gateway via neighbor advertisements.
        """
        # spoof clients with GARP broadcast request
        with self.sleeper:
            if self.ipv4:
                sendp(
                    Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.ipv4.gateway, pdst=self.ipv4.gateway, hwdst=ETHER_BROADCAST,
                                                     hwsrc=self.ipv4.gate_mac))
            if self.ipv6:
                # check if the impersonation of the DNS server is necessary
                tgt = (self.ipv6.gateway, self.ipv6.dns_servers[0]) if util.is_spoof_dns(self.ipv6) else (self.ipv6.gateway,)

                for source in tgt:
                    sendp(Ether(dst=ETHER_BROADCAST) / IPv6(src=source, dst=MulticastPingDiscoveryThread._MULTICAST_DEST) /
                          ICMPv6ND_NA(tgt=source, R=0, S=0) / ICMPv6NDOptDstLLAddr(lladdr=self.ipv6.gate_mac))

    def exit(self, signal_number, stack_frame):
        """This method is called from the python-daemon when the daemon is stopping.
        Threads are stopped and clients are despoofed via _return_to_normal().
        """
        self._return_to_normal()
        raise SystemExit()

    def run(self):
        """Starts multiple threads sends out packets to spoof
        all existing clients on the network and the gateway. This packets are sent every __SLEEP seconds.
        The existing clients (device entries) are read from the redis database.

        Threads:
            A SniffThread, which sniffs for incoming ARP packets and adds new devices to the redis db.
            Several HostDiscoveryThread, which are searching for existing devices on the network.
            A PubSubThread, which is listening for redis expiry messages.

        Note:
            First, ARP replies to spoof the gateway entry of existing clients arp cache are generated.
            ARP relpies to spoof the entries of the gateway are generated next.
            Unlike the holistic mode only packets for existing clients are generated.

        """
        self.threads['sniffthread'].start()
        if self.ipv4:
            self.threads['arpthread'].start()
            self.threads['psthread'].start()
            self.threads['igmpthread'].start()
        if self.ipv6:
            self.threads['icmpv6thread'].start()
            self.threads['mldv2thread'].start()
            self.threads['psthread6'].start()

        # lamda expression to generate arp replies to spoof the clients
        if self.ipv4:
            exp1 = lambda dev: Ether(dst=dev[1]) / ARP(op=2, psrc=self.ipv4.gateway, pdst=dev[0], hwdst=dev[1])

        # lamda expression to generate arp replies to spoof the gateway
        # exp2 = lambda dev: Ether(dst=self.gate_mac) / ARP(op=2, psrc=dev[0], pdst=self.gateway, hwdst=self.gate_mac

        while True:
            packets = []
            # generates packets for existing clients
            # due to the labda expressions p1 and p2 this list comprehension, each iteration generates 2 packets
            # one to spoof the client and one to spoof the gateway
            if self.ipv4:
                packets.extend([p(dev) for dev in self.ipv4.redis.get_devices_values(filter_values=True) for p in (exp1,)])  # if dev[0] != self.gateway]
            #packets = [p(dev) for dev in self.redis.get_devices_values(filter_values=True) for p in (exp1, exp2) if dev[0] != self.gateway]
            if self.ipv6:
                # check if the impersonation of the DNS server is necessary
                tgt = (self.ipv6.gateway, self.ipv6.dns_servers[0]) if util.is_spoof_dns(self.ipv6) else (self.ipv6.gateway,)

                for source in tgt:
                    packets.extend([Ether(dst=dev[1]) / IPv6(src=source, dst=dev[0]) /
                                    ICMPv6ND_NA(tgt=source, R=0, S=1) / ICMPv6NDOptDstLLAddr(lladdr=self.ipv6.mac)
                                    for dev in self.ipv6.redis.get_devices_values(filter_values=True)])

            sendp(packets)
            try:
                with self.sleeper:
                    self.sleeper.wait(timeout=self.__SLEEP)
            except RuntimeError as e:
                # this error is thrown by the with-statement when the thread is stopped
                if len(e.args) > 0 and e.args[0] == "cannot release un-acquired lock":
                    return
                else:
                    raise e

class DaemonError(Exception):
    """This error class indicates, that the daemon has failed."""
    pass
