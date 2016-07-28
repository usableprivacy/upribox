# coding=utf-8
"""This module provides several classes that are used to implement a ARP spoofing daemon.

Classes:
    _DaemonApp: Abstract class, that should be inherited.
    HolisticDaemonApp: Inherits _DaemonApp and implements the holistist spoofing mode.
    SelectiveDaemonApp: Inherits _DaemonApp and implements the selective spoofing mode.
    DaemonError: Error that indicates the daemon's failure.
    DiscoveryThread: Discovers clients on the network by sending out ARP request.
    PubSubThread: Listens for redis expiry messages and removes expired devices.

"""
import os
import logging
import time
import threading
import netifaces as ni
from netaddr import IPAddress, IPNetwork, AddrFormatError

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import conf, sendp, ARP, Ether, ETHER_BROADCAST

import util
from sniff_thread import HolisticSniffThread, SelectiveSniffThread
from apate_redis import ApateRedis


class _DaemonApp(object):
    """This is an abstract class, which should be inherited to define the
    Apate daemon's behaviour."""

    def __init__(self, logger, interface, pidfile, stdout, stderr):
        """Initialises several things needed to define the daemons behaviour.

        Args:
            logger (logging.Logger): Used for logging messages.
            interface (str): The network interface which should be used. (e.g. eth0)
            pidfile (str): Path of the pidfile, used by the daemon.
            stdout (str): Path of stdout, used by the daemon.
            stderr (str): Path of stderr, used by the daemon.

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

        if_info = None
        try:
            if_info = ni.ifaddresses(self.interface)
        except ValueError as e:
            self.logger.error("An error concerning the interface {} has occurred: {}".format(self.interface, str(e)))
            raise DaemonError()

        # get ip of specified interface
        self.ip = if_info[2][0]['addr']
        # get subnetmask of specified interface
        self.netmask = if_info[2][0]['netmask']
        # get mac address of specified interface
        self.mac = if_info[17][0]['addr']

        # get network address
        try:
            self.network = IPNetwork("{}/{}".format(self.ip, self.netmask))
        except AddrFormatError as afe:
            # this should never happen, because values are retrieved via netifaces library
            self.logger.error("A grave error happened during determinig the network: {}".format(str(afe)))
            raise DaemonError()

        # get default gateway
        try:
            self.gateway = ni.gateways()["default"][ni.AF_INET][0]
        except KeyError:
            self.logger.error("No default gateway is configured")
            raise DaemonError()

        # get all ip addresses that are in the specified network
        # and remove network address, broadcast, own ip, gateway ip
        self.ip_range = list(self.network)
        self.ip_range.remove(IPAddress(self.ip))
        self.ip_range.remove(IPAddress(self.gateway))
        self.ip_range.remove(IPAddress(self.network.broadcast))
        self.ip_range.remove(IPAddress(self.network.network))

        try:
            # get MAC address of gateway
            self.gate_mac = util.get_mac(self.gateway, self.interface)
            if not self.gate_mac:
                raise DaemonError()
        except Exception:
            self.logger.error("Unable to get MAC address of Gateway")
            raise DaemonError()

    def __return_to_normal(self):
        """This method should be overriden to define the actions to be done when stopping the daemon."""
        pass

    def exit(self, signal_number, stack_frame):
        """This method is called if the daemon stops."""
        self.__return_to_normal()
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

    def __init__(self, logger, interface, pidfile, stdout, stderr):
        """Initialises several things needed to define the daemons behaviour.

        Args:
            logger (logging.Logger): Used for logging messages.
            interface (str): The network interface which should be used. (e.g. eth0)
            pidfile (str): Path of the pidfile, used by the daemon.
            stdout (str): Path of stdout, used by the daemon.
            stderr (str): Path of stderr, used by the daemon.

        Raises:
            DaemonError: Signalises the failure of the daemon.
        """
        super(self.__class__, self).__init__(logger, interface, pidfile, stdout, stderr)

        self.sniffthread = HolisticSniffThread(self.interface, self.gateway, self.mac, self.gate_mac)
        self.sniffthread.daemon = True

    def __return_to_normal(self):
        """This method is called when the daemon is stopping.
        First, sends a GARP broadcast request to all clients to tell them the real gateway.
        Then an ARP request is sent to every client, so that they answer the real gateway and update its ARP cache.
        """
        # clients gratutious arp
        sendp(
            Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.gateway, hwdst=ETHER_BROADCAST,
                                             hwsrc=self.gate_mac))
        # to clients so that they send and arp reply to the gateway
        sendp(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=str(self.network), hwsrc=self.gate_mac))

    def exit(self, signal_number, stack_frame):
        """This method is called from the python-daemon when the daemon is stopping.
        Threads are stopped and clients are despoofed via __return_to_normal().
        """
        self.__return_to_normal()
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
        packets = [Ether(dst=self.gate_mac) / ARP(op=1, psrc=str(x), pdst=str(x)) for x in self.ip_range]
        # gratuitous arp to clients
        # updates the gateway entry of the clients arp table
        packets.append(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.gateway,
                                                        hwdst=ETHER_BROADCAST))
        while True:
            sendp(packets)
            time.sleep(self.__SLEEP)


class SelectiveDaemonApp(_DaemonApp):
    """Implements the abstract class _DaemonApp and also implements the selective spoofing mode of Apate.
    The selective spoofing mode requires more resources than the holistic spoofing mode,
    e.g.: the redis-server. This mode only generates packets for existing clients (not every possible client).
    This mode is suitable for bigger networks, as the bottleneck of this mode is virtually only the host discovery.
    """

    __SLEEP = 5
    """int: Defines the time to sleep after packets are sent before they are sent anew."""

    def __init__(self, logger, interface, pidfile, stdout, stderr):
        """Initialises several things needed to define the daemons behaviour.

        Args:
            logger (logging.Logger): Used for logging messages.
            interface (str): The network interface which should be used. (e.g. eth0)
            pidfile (str): Path of the pidfile, used by the daemon.
            stdout (str): Path of stdout, used by the daemon.
            stderr (str): Path of stderr, used by the daemon.

        Raises:
            DaemonError: Signalises the failure of the daemon.
        """
        super(self.__class__, self).__init__(logger, interface, pidfile, stdout, stderr)
        self.redis = ApateRedis(str(self.network.network), logger)

        # Initialise threads
        self.sniffthread = SelectiveSniffThread(self.interface, self.gateway, self.mac, self.gate_mac, self.redis)
        self.sniffthread.daemon = True
        self.psthread = PubSubThread(self.redis, self.logger)
        self.psthread.daemon = True
        self.discoverythread = DiscoveryThread(self.gateway, str(self.network.network))
        self.discoverythread.daemon = True

    def __return_to_normal(self):
        """This method is called when the daemon is stopping.
        First, sends a GARP broadcast request to all clients to tell them the real gateway.
        Then ARP replies for existing clients are sent to the gateway.
        """
        # spoof clients with GARP boradcast request
        sendp(
            Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.gateway, hwdst=ETHER_BROADCAST,
                                             hwsrc=self.gate_mac))

        # generate ARP reply packet for every existing client and spoof the gateway
        packets = [Ether(dst=self.gate_mac) / ARP(op=2, psrc=dev[0], pdst=self.gateway, hwsrc=dev[1]) for dev in self.redis.get_devices_values(filter_values=True)]
        sendp(packets)

    def exit(self, signal_number, stack_frame):
        """This method is called from the python-daemon when the daemon is stopping.
        Threads are stopped and clients are despoofed via __return_to_normal().
        """
        self.__return_to_normal()
        raise SystemExit()

    def run(self):
        """Starts multiple threads sends out packets to spoof
        all existing clients on the network and the gateway. This packets are sent every __SLEEP seconds.
        The existing clients (device entries) are read from the redis database.

        Threads:
            A SniffThread, which sniffs for incoming ARP packets and adds new devices to the redis db.
            A HostDiscoveryThread, which is searching for existing devices on the network.
            A PubSubThread, which is listening for redis expiry messages.

        Note:
            First, ARP replies to spoof the gateway entry of existing clients arp cache are generated.
            ARP relpies to spoof the entries of the gateway are generated next.
            Unlike the holistic mode only packets for existing clients are generated.

        """
        self.sniffthread.start()
        self.discoverythread.start()
        self.psthread.start()

        # lamda expression to generate arp replies to spoof the clients
        exp1 = lambda dev: Ether(dst=dev[1]) / ARP(op=2, psrc=self.gateway, pdst=dev[0], hwdst=dev[1])

        # lamda expression to generate arp replies to spoof the gateway
        exp2 = lambda dev: Ether(dst=self.gate_mac) / ARP(op=2, psrc=dev[0], pdst=self.gateway, hwdst=self.gate_mac)

        while True:
            # generates packets for existing clients
            # due to the labda expressions p1 and p2 this list comprehension, each iteration generates 2 packets
            # one to spoof the client and one to spoof the gateway
            packets = [p(dev) for dev in self.redis.get_devices_values(filter_values=True) for p in (exp1, exp2)]

            sendp(packets)
            time.sleep(self.__SLEEP)


class DaemonError(Exception):
    """This error class indicates, that the daemon has failed."""
    pass


class DiscoveryThread(threading.Thread):
    """This thread is used to discovery clients on the network by sending ARP requests."""

    def __init__(self, gateway, network):
        """Initialises the thread.

        Args:
            gateway (str): The gateways IP address.
            network (str): The network IP address.s

        """
        threading.Thread.__init__(self)
        self.gateway = gateway
        self.network = network

    def run(self):
        """Sends broadcast ARP requests for every possible client of the network.
        Received ARP replies are processed by a SniffThread.
        """
        sendp(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.network))


class PubSubThread(threading.Thread):
    """This thread is used to listen for redis expiry keyspace event messages."""

    __SUBSCRIBE_TO = "__keyevent@5__:expired"
    """Used to subscribe to the keyspace event expired."""

    def __init__(self, redis, logger):
        """Initialises the thread.

        Args:
            redis (apate_redis.ApateRedis): Used for obtaining the required PubSub object.
            logger (logging.Logger): Used to log messages.

        """
        threading.Thread.__init__(self)
        self.redis = redis
        self.logger = logger
        self.pubsub = self.redis.get_pubsub()

    def run(self):
        """Subscribes to redis expiry keyspace events and removes the ip address of the expired device from the network set."""
        self.pubsub.subscribe(self.__SUBSCRIBE_TO)
        for message in self.pubsub.listen():
            self.logger.debug("Removed expired device {} from network {}".format(util.get_device_ip(message['data']), util.get_device_net(message['data'])))
            # removes the ip of the expired device (the removed device entry) from the network set
            self.redis._del_device_from_network(util.get_device_ip(message['data']), util.get_device_net(message['data']))

    def stop(self):
        """Closes the connection of the PubSub object."""
        self.pubsub.close()
