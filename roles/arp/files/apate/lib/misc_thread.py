# coding=utf-8
"""This module provides several threads used by the ARP spoofing daemon.

Classes:
    ARPDiscoveryThread: Discovers clients on the network by sending out ARP request.
    IGMPDiscoveryThread: Discovers clients on the network by sending out IGMP general queries.
    PubSubThread: Listens for redis expiry messages and removes expired devices.

"""
import time
import threading
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import conf, sendp, ARP, Ether, ETHER_BROADCAST, IP
from scapy.contrib.igmp import IGMP
import util


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

    def __init__(self, gateway, network, ip, mac):
        """Initialises the thread.

        Args:
            gateway (str): The gateway's IP address.
            network (str): The network IP address.
            mac (str): MAC address of this device.
            ip (str): IP address of this device.

        """
        threading.Thread.__init__(self)
        self.gateway = gateway
        self.network = network
        self.mac = mac
        self.ip = ip

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
