# coding=utf-8
"""This module provides several classes that are used to implement
a thread that listens to incoming ARP packets.

Classes:
    _SniffThread: Abstract class, that should be inherited.
    HolisticSniffThread: Inherits _SniffThread and implements the holistist spoofing listener.
    SelectiveSniffThread: Inherits _SniffThread and implements the selective spoofing listener.

"""
import logging
import thread
import threading

import util
from misc_thread import MulticastPingDiscoveryThread
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import (ARP, ETHER_BROADCAST, IP, Ether, ICMPv6EchoReply,
                       ICMPv6MLReport, ICMPv6ND_NA, ICMPv6ND_RA,
                       ICMPv6NDOptDstLLAddr, IPv6, sendp, sniff)
from scapy.contrib.igmp import IGMP

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)


class _SniffThread(threading.Thread):
    """This is an abstract class, which should be inherited to define the
    behaviour fo the sniffing thread."""

    _DELAY = 7.0
    """float: Delay after which packets are sent."""
    _SNIFF_FILTER = "arp and inbound"
    """str: tcpdump filter used for scapy's sniff function."""
    _LFILTER = staticmethod(lambda x: x.haslayer(ARP))
    """function: lambda filter used for scapy's sniff function."""

    def __init__(self, interface, ip):
        """Initialises several things needed to define the thread's behaviour.

        Args:
            interface (str): The network interface which should be used. (e.g. eth0)
            ipv4 (namedtuple): Contains several information about the ipv4 configuration.
            ipv6 (namedtuple): Contains several information about the ipv6 configuration.
        """
        threading.Thread.__init__(self)
        self.interface = interface
        self.ip = ip

    def run(self):
        """Starts sniffing for incoming ARP packets with scapy.
        Actions after receiving a packet ar defines via _packet_handler.
        """
        # the filter argument in scapy's sniff function seems to be applied too late
        # therefore some unwanted packets are processed (e.g. tcp packets of ssh session)
        # but it still decreases the number of packets that need to be processed by the lfilter function
        sniff(prn=self._packet_handler, filter=self._SNIFF_FILTER, lfilter=self._LFILTER, store=0, iface=self.interface)

    def _packet_handler(self, pkt):
        """This method should be overriden to define the thread's behaviour."""
        pass

    @staticmethod
    def stop():
        """May be used to kill the thread, if it is not a daemon thread."""
        thread.exit()


class HolisticSniffThread(_SniffThread):
    """Implements the abstract class _SniffThread and also implements
    the listener of the holistic spoofing mode of Apate.
    """

    def __init__(self, interface, ipv4, logger):
        """Initialises several things needed to define the thread's behaviour.

        Args:
            interface (str): The network interface which should be used. (e.g. eth0)
            ipv4 (namedtuple): Contains several information about the ipv4 configuration.
            ipv6 (namedtuple): Contains several information about the ipv6 configuration.
        """
        super(HolisticSniffThread, self).__init__(interface, ipv4)
        self.logger = logger

    def _packet_handler(self, pkt):
        """This method is called for each packet received through scapy's sniff function.
        Incoming ARP requests are used to spoof involved devices.

        Args:
            pkt (str): Received packet via scapy's sniff (through socket.recv).
        """
        try:
            # when ARP request
            if pkt[ARP].op == 1:

                # packets intended for this machine (upribox)
                if pkt[Ether].dst == self.ip.mac:
                    # incoming packets(that are sniffed): Windows correctly fills in the hwdst, linux (router) only 00:00:00:00:00:00
                    # this answers packets asking if we are the gateway (directly not via broadcast)
                    # Windows does this 3 times before sending a broadcast request
                    sendp(Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwdst=pkt[ARP].hwsrc, hwsrc=self.ip.mac))

                # broadcast request to gateway
                elif pkt[Ether].dst.lower() == util.hex2str_mac(ETHER_BROADCAST) and (pkt[ARP].pdst == self.ip.gateway):
                    # pkt[ARP].psrc == self.gateway or

                    # spoof transmitter
                    packets = [Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwsrc=self.ip.mac, hwdst=pkt[ARP].hwsrc)]

                    # some os didn't accept an answer immediately (after sending the first ARP request after boot
                    # so, send packets after some delay
                    threading.Timer(self._DELAY, sendp, [packets]).start()
                    # TODO gratuitous neighbor advertisements
        except Exception as e:
            self.logger.error("Failed to handle packet")
            self.logger.exception(e)


class _SelectiveSniffThread(_SniffThread):
    """Implements the abstract class _SniffThread and also implements
    the listener of the selective spoofing mode of Apate.
    """
    _SNIFF_PARTS = []
    """list: List of tuples containing a BFP filter and the according scapy class."""

    _SNIFF_DIRECTION = "inbound"
    """str: speficies which traffic should be sniffed."""

    _SNIFF_FILTER = lambda self: "({}) and {}".format(" or ".join(zip(*self._SNIFF_PARTS)[0]), self._SNIFF_DIRECTION)
    """str: tcpdump filter used for scapy's sniff function."""
    # _SNIFF_FILTER = "(arp or igmp or (icmp6 and ip6[40] == 129) or (multicast and ip6[48] == 131) or (icmp6 and ip6[40] == 134)) and inbound"

    _LFILTER = lambda self, x: any([x.haslayer(layer) for layer in zip(*self._SNIFF_PARTS)[1]])
    # _LFILTER = staticmethod(lambda x: any([x.haslayer(layer) for layer in (ARP, IGMP, ICMPv6EchoReply, ICMPv6MLReport, ICMPv6ND_RA)]))
    """function: lambda filter used for scapy's sniff function."""

    def __init__(self, interface, ip, sleeper, logger):
        """Initialises several things needed to define the thread's behaviour.

        Args:
            interface (str): The network interface which should be used. (e.g. eth0)
            ipv4 (namedtuple): Contains several information about the ipv4 configuration.
            ipv6 (namedtuple): Contains several information about the ipv6 configuration.
            sleeper (threading.Condition): Used for thread synchronisation.

        """
        super(_SelectiveSniffThread, self).__init__(interface, ip)
        self.sleeper = sleeper
        self.logger = logger

    def run(self):
        """Starts sniffing for incoming ARP packets with scapy.
        Actions after receiving a packet ar defines via _packet_handler.
        """
        # the filter argument in scapy's sniff function seems to be applied too late
        # therefore some unwanted packets are processed (e.g. tcp packets of ssh session)
        # but it still decreases the number of packets that need to be processed by the lfilter function
        sniff(prn=self._packet_handler, filter=self._SNIFF_FILTER(), lfilter=self._LFILTER, store=0, iface=self.interface)


class SelectiveIPv4SniffThread(_SelectiveSniffThread):
    """Implements the abstract class _SniffThread and also implements
    the listener of the selective spoofing mode of Apate.
    """
    _SNIFF_PARTS = [
        ("arp", ARP),
        ("igmp", IGMP),
    ]
    """list: List of tuples containing a BFP filter and the according scapy class."""

    def __init__(self, interface, ip, sleeper, logger):
        super(SelectiveIPv4SniffThread, self).__init__(interface, ip, sleeper, logger)

    def _packet_handler(self, pkt):
        """This method is called for each packet received through scapy's sniff function.

        Args:
            pkt (str): Received packet via scapy's sniff (through socket.recv).
        """
        try:
            if self.ip and pkt.haslayer(Ether) and pkt[Ether].src != self.ip.gate_mac:
                if pkt.haslayer(ARP):
                    self._arp_handler(pkt)
                elif pkt.haslayer(IGMP):
                    self._igmp_handler(pkt)
        except Exception as e:
            self.logger.error("Failed to handle packet")
            self.logger.exception(e)

    def _arp_handler(self, pkt):
        """"This method is called for each incoming ARP packet received through scapy's sniff function.
        Incoming ARP requests are used to spoof involved devices and add new devices
        to the redis db. New devices are also added if ARP replies are received.

        Args:
            pkt (str): Received packet via scapy's sniff (through socket.recv).
        """
        # when ARP request
        if pkt[ARP].op == 1:
            # packets intended for this machine (upribox)
            if pkt[Ether].dst == self.ip.mac:
                # incoming packets(that are sniffed): Windows correctly fills in the hwdst, linux (router) only 00:00:00:00:00:00
                # this answers packets asking if we are the gateway (directly not via broadcast)
                # Windows does this 3 times before sending a broadcast request
                if not self.ip.redis.check_device_disabled(pkt[ARP].hwsrc):
                    sendp(Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwdst=pkt[ARP].hwsrc, hwsrc=self.ip.mac))
                # add transmitting device to redis db
                self.ip.redis.add_device(pkt[ARP].psrc, pkt[ARP].hwsrc)

            # broadcast request to gateway
            elif pkt[Ether].dst.lower() == util.hex2str_mac(ETHER_BROADCAST) and (pkt[ARP].pdst == self.ip.gateway):
                # pkt[ARP].psrc == self.gateway or

                # spoof transmitter
                packets = [Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwsrc=self.ip.mac, hwdst=pkt[ARP].hwsrc)]

                # add transmitting device to redis db
                self.ip.redis.add_device(pkt[ARP].psrc, pkt[ARP].hwsrc)

                # some os didn't accept an answer immediately (after sending the first ARP request after boot
                # so, send packets after some delay
                if not self.ip.redis.check_device_disabled(pkt[ARP].hwsrc):
                    threading.Timer(self._DELAY, sendp, [packets]).start()
        else:
            # ARP reply
            # add transmitting device to redis db
            if not self.ip.redis.check_device_disabled(pkt[ARP].hwsrc):
                self.ip.redis.add_device(pkt[ARP].psrc, pkt[ARP].hwsrc)

    def _igmp_handler(self, pkt):
        """"This method is called for each IGMP packet received through scapy's sniff function.
        Incoming IGMP answers are used to spoof involved devices and add new devices
        to the redis db.

        Args:
            pkt (str): Received packet via scapy's sniff (through socket.recv).
        """
        self.ip.redis.add_device(pkt[IP].src, pkt[Ether].src)
        if not self.ip.redis.check_device_disabled(pkt[Ether].src):
            sendp(Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=self.ip.gateway, pdst=pkt[IP].src, hwdst=pkt[Ether].src))


class SelectiveIPv6SniffThread(_SelectiveSniffThread):
    """Implements the abstract class _SniffThread and also implements
    the listener of the selective spoofing mode of Apate.
    """
    _SNIFF_PARTS = [
        # icmpv6 echo reply
        ("(icmp6 and ip6[40] == 129)", ICMPv6EchoReply),
        # mldv2 multicast listener report
        ("(multicast and ip6[48] == 131)", ICMPv6MLReport),
        # router advertisement
        ("(icmp6 and ip6[40] == 134)", ICMPv6ND_RA)
    ]
    """list: List of tuples containing a BFP filter and the according scapy class."""

    def __init__(self, interface, ip, sleeper, logger):
        super(SelectiveIPv6SniffThread, self).__init__(interface, ip, sleeper, logger)

    def _packet_handler(self, pkt):
        """This method is called for each packet received through scapy's sniff function.

        Args:
            pkt (str): Received packet via scapy's sniff (through socket.recv).
        """
        try:
            if self.ip and pkt.haslayer(Ether) and pkt[Ether].src != self.ip.gate_mac:
                if pkt.haslayer(ICMPv6EchoReply) and pkt[ICMPv6EchoReply].data == MulticastPingDiscoveryThread._DATA:
                    # react to echo replies with data == upribox
                    self._icmpv6_handler(pkt)
                elif pkt.haslayer(ICMPv6MLReport):
                    # react to multicast listener reports
                    self._icmpv6_handler(pkt)
                elif pkt.haslayer(ICMPv6ND_RA):
                    # spoof clients after receiving a router advertisement
                    with self.sleeper:
                        self.sleeper.notifyAll()
        except Exception as e:
            self.logger.error("Failed to handle packet")
            self.logger.exception(e)

    def _icmpv6_handler(self, pkt):
        """"This method is called for each ICMPv6 echo reply packet or multicast listener report packet
        received through scapy's sniff function.
        Incoming packets are used to spoof involved devices and add new devices
        to the redis db.

        Args:
            pkt (str): Received packet via scapy's sniff (through socket.recv).
        """
        # add transmitting device to redis db
        self.ip.redis.add_device(pkt[IPv6].src, pkt[Ether].src)
        # impersonate gateway
        if not self.ip.redis.check_device_disabled(pkt[Ether].src):
            sendp(
                Ether(dst=pkt[Ether].src) / IPv6(src=self.ip.gateway, dst=pkt[IPv6].src) / ICMPv6ND_NA(tgt=self.ip.gateway, R=0, S=1) /
                ICMPv6NDOptDstLLAddr(lladdr=self.ip.mac)
            )

        # impersonate DNS server if necessary
        if util.is_spoof_dns(self.ip):
            if not self.ip.redis.check_device_disabled(pkt[Ether].src):
                sendp(
                    Ether(dst=pkt[Ether].src) / IPv6(src=self.ip.dns_servers[0], dst=pkt[IPv6].src) /
                    ICMPv6ND_NA(tgt=self.ip.dns_servers[0], R=0, S=1) / ICMPv6NDOptDstLLAddr(lladdr=self.ip.mac)
                )
