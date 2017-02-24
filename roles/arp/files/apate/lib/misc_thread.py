# coding=utf-8
"""This module provides several threads used by the ARP spoofing daemon.

Classes:
    ARPDiscoveryThread: Discovers clients on the network by sending out ARP request.
    IGMPDiscoveryThread: Discovers clients on the network by sending out IGMP general queries.
    PubSubThread: Listens for redis expiry messages and removes expired devices.
    MulticastPingDiscoveryThread: Discovers clients on the network by sending out multicast echo requests.
    MulticastListenerDiscoveryThread: Discovers clients on the network by sending out MLDv2 queries.

"""
import time
import threading
import logging
import util
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import conf, sendp, send, ARP, Ether, ETHER_BROADCAST, IP, IPv6, ICMPv6EchoRequest, IPv6ExtHdrHopByHop, RouterAlert, ICMPv6MLQuery
from scapy.contrib.igmp import IGMP


class ARPDiscoveryThread(threading.Thread):
    """This thread is used to discover clients on the network by sending ARP requests."""

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


class MulticastPingDiscoveryThread(threading.Thread):
    """This thread is used to discover clients on the network by sending ICMPv6 Multicast Pings."""
    _MULTICAST_DEST = "ff02::1"
    """str: IPv6 all nodes multicast address."""
    # RFC 4443: The data received in the ICMPv6 Echo Request message MUST be returned
    # entirely and unmodified in the ICMPv6 Echo Reply message.
    _DATA = "upribox"
    """str: This data is used to identify echo replies."""
    _SLEEP = 60
    """int: Time to wait before sending packets anew."""

    def __init__(self):
        """Initialises the thread.
        """
        threading.Thread.__init__(self)

    def run(self):
        """Sends ICMPv6 echo request packets marked with the data upribox to the
        IPv6 all nodes multicast address.
        Received echo replies are processed by a SniffThread.
        """
        while True:
            send(IPv6(dst=self._MULTICAST_DEST) / ICMPv6EchoRequest(data=self._DATA))
            time.sleep(self._SLEEP)


class IGMPDiscoveryThread(threading.Thread):
    """This thread is used to discover clients on the network by sending IGMP general queries."""

    _IGMP_MULTICAST = "224.0.0.1"
    """str: Multicast address used to send IGMP general queries."""
    _SLEEP = 60
    """int: Time to wait before sending packets anew."""
    _IGMP_GENERAL_QUERY = 0x11
    """int: Value of type Field for IGMP general queries."""
    _TTL = 1
    """int: Value for TTL for IP packet."""

    def __init__(self, ipv4):
        """Initialises the thread.

        Args:
            ipv4 (namedtuple): Contains various information about the IPv4 configuration.
            ipv4.gateway (str): The gateway's IP address.
            ipv4.network (netaddr.IPNetwork): The network IP address.
            ipv4.mac (str): MAC address of this device.
            ipv4.ip (str): IP address of this device.

        """
        threading.Thread.__init__(self)
        self.gateway = ipv4.gateway
        self.network = str(ipv4.network.network)
        self.mac = ipv4.mac
        self.ip = ipv4.ip

    def run(self):
        """Sends IGMP general query packets using the multicast address 224.0.0.1.
        Received replies are processed by a SniffThread.
        """

        # create IGMP general query packet
        ether_part = Ether(src=self.mac)
        ip_part = IP(ttl=self._TTL, src=self.ip, dst=self._IGMP_MULTICAST)
        igmp_part = IGMP(type=self._IGMP_GENERAL_QUERY)

        # Called to explicitely fixup associated IP and Ethernet headers
        igmp_part.igmpize(ether=ether_part, ip=ip_part)

        while True:
            sendp(ether_part / ip_part / igmp_part)
            time.sleep(self._SLEEP)


class PubSubThread(threading.Thread):
    """This thread is used to listen for redis expiry keyspace event messages."""

    __SUBSCRIBE_TO = "__keyevent@{}__:expired"
    """Used to subscribe to the keyspace event expired."""
    __SUBSCRIBE_TOO = "__keyspace@{}__:{}"

    def __init__(self, ip, logger, handler):
        """Initialises the thread.

        Args:
            redis (apate_redis.ApateRedis): Used for obtaining the required PubSub object.
            logger (logging.Logger): Used to log messages.

        """
        threading.Thread.__init__(self)
        self.ip = ip
        self.redis = ip.redis
        self.logger = logger
        self.pubsub = self.redis.get_pubsub()
        #self.sleeper = sleeper
        self.handler = handler

    def run(self):
        """Subscribes to redis expiry keyspace events and removes the ip address of the expired device from the network set."""
        self.pubsub.subscribe(**{self.__SUBSCRIBE_TO.format(self.redis.get_database()): self._handle_expired,
                                 self.__SUBSCRIBE_TOO.format(self.redis.get_database(), self.redis.get_toggled_key()): self._handle_toggled})
        for message in self.pubsub.listen():
            pass

    def _handle_expired(self, message):
        self.logger.debug("Removed expired device {} from network {}".format(util.get_device_ip(message['data']), util.get_device_net(message['data'])))
        # removes the ip of the expired device (the removed device entry) from the network set
        self.redis._del_device_from_network(util.get_device_ip(message['data']), util.get_device_net(message['data']))

    def _handle_toggled(self, message):
        if message['data'] == 'sadd':
            # devs can be used to selectively spoof only the toggled devices
            devs = self.redis.pop_toggled()
            self.handler(self.ip, devs, self.logger)

    def stop(self):
        """Closes the connection of the PubSub object."""
        self.pubsub.close()


class MulticastListenerDiscoveryThread(threading.Thread):
    """This thread is used to discover clients on the network by sending ICMPv6 MLDv2 Queries."""
    _MULTICAST_DEST = "ff02::1"
    """str: IPv6 all nodes multicast address."""
    _HOP_LIMIT = 1
    """int: Speficies the Hop Limit parameter for the IPv6 packet field."""
    _SLEEP = 60
    """int: Time to wait before sending packets anew."""

    def __init__(self):
        """Initialises the thread.
        """
        threading.Thread.__init__(self)

    def run(self):
        """Sends Multicast Listener Discovery Queries to all nodes on the network.
        Received Multicast Listener Reports are processed by a SniffThread.
        """
        while True:
            send(IPv6(dst=self._MULTICAST_DEST, hlim=self._HOP_LIMIT) / IPv6ExtHdrHopByHop(options=RouterAlert()) / ICMPv6MLQuery())
            time.sleep(self._SLEEP)
