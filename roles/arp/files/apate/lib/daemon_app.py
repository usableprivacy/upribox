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
import collections
import dns.resolver
import netifaces as ni
from netaddr import IPAddress, IPNetwork, AddrFormatError

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import conf, sendp, ARP, Ether, ETHER_BROADCAST

import util
from sniff_thread import HolisticSniffThread
from daemon_process import SelectiveIPv4Process, SelectiveIPv6Process


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
            ip = if_info[ni.AF_INET][-1]['addr']
            # get subnetmask of specified interface
            netmask = if_info[ni.AF_INET][-1]['netmask'].split("/")[0]
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

            # get all ipv4 nameservers
            dns_servers = [x for x in rs.nameservers if IPAddress(x).version == 4 and not IPAddress(x).is_reserved()]
            # store ipv4 information
            self.ipv4 = IPInfo(ip, netmask, network, gateway, mac, gate_mac, dns_servers, None)
        except AddrFormatError as afe:
            # this should never happen, because values are retrieved via netifaces library
            self.logger.error("A error happened during determinig the IPv4 network: {}".format(str(afe)))
        except KeyError:
            self.logger.debug("No IPv4 default gateway is configured")
        except IndexError:
            self.logger.debug("No IPv4 address is configured")

        try:
            # global IPv6 if self.ipv6 results in True
            # get ipv6 addresses of specified interface
            ip = [x for x in if_info[ni.AF_INET6] if not IPAddress(x['addr'].split("%")[0]).is_private()]
            #self.linklocal = [x['addr'].split("%")[0] for x in if_info[ni.AF_INET6] if IPAddress(x['addr'].split("%")[0]).is_link_local()][0]

            # get network address
            network = IPNetwork("{}/{}".format(ip[0]['addr'], ip[0]['netmask'].split("/")[0]))
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

            # get all ipv6 nameservers
            dns_servers = [x for x in rs.nameservers if IPAddress(x).version == 6 and not IPAddress(x).is_reserved()]
            # store ipv6 information
            self.ipv6 = IPInfo(ip, netmask, network, gateway, mac, gate_mac, dns_servers, None)
        except AddrFormatError as afe:
            # this should never happen, because values are retrieved via netifaces library
            self.logger.error("A error happened during determinig the IPv6 network: {}".format(str(afe)))
        except KeyError:
            self.logger.debug("No IPv6 default gateway is configured")
        except IndexError:
            self.logger.debug("No IPv6 address is configured")

        if not any((self.ipv4, self.ipv6)):
            # at least ipv4 or ipv6 has to be configured
            self.logger.error("Unable to retriev IPv4 and IPv6 configuration")
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

        self.sniffthread = HolisticSniffThread(self.interface, self.ipv4, logger)
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
        self.processv4 = None
        self.processv6 = None

    def exit(self, signal_number, stack_frame):
        """This method is called from the python-daemon when the daemon is stopping.
        Threads are stopped and clients are despoofed via _return_to_normal().
        """
        if self.processv4:
            self.processv4.shutdown()

        if self.processv6:
            self.processv6.shutdown()

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

        # a child-process object has to be created in the same parent process as the process that wants to start the child
        # __init__ is called inside the initial process, whereas run() is called inside the newly created deamon process
        # therefore create the process here
        if self.ipv4:
            self.processv4 = SelectiveIPv4Process(self.logger, self.interface, self.ipv4)
            self.processv4.start()

        if self.ipv6:
            self.processv6 = SelectiveIPv6Process(self.logger, self.interface, self.ipv6)
            self.processv6.start()

        if self.processv4:
            self.processv4.join()
        if self.processv6:
            self.processv6.join()


class DaemonError(Exception):
    """This error class indicates, that the daemon has failed."""
    pass
