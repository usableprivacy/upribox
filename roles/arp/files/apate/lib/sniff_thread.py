# coding=utf-8
"""This module provides several classes that are used to implement
a thread that listens to incoming ARP packets.

Classes:
    _SniffThread: Abstract class, that should be inherited.
    HolisticSniffThread: Inherits _SniffThread and implements the holistist spoofing listener.
    SelectiveSniffThread: Inherits _SniffThread and implements the selective spoofing listener.

"""
import thread
import logging
import threading

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import sendp, ARP, Ether, IP, ETHER_BROADCAST, sniff, ICMPv6EchoReply, IPv6, ICMPv6MLReport, ICMPv6ND_RA, ICMPv6NDOptDstLLAddr, ICMPv6ND_NA
from scapy.contrib.igmp import IGMP

import util
from misc_thread import MulticastPingDiscoveryThread


class _SniffThread(threading.Thread):
    """This is an abstract class, which should be inherited to define the
    behaviour fo the sniffing thread."""

    _DELAY = 7.0
    """float: Delay after which packets are sent."""
    _SNIFF_FILTER = "arp and inbound"
    """str: tcpdump filter used for scapy's sniff function."""
    _LFILTER = staticmethod(lambda x: x.haslayer(ARP))
    """function: lambda filter used for scapy's sniff function."""

    def __init__(self, interface, ipv4, ipv6):
        """Initialises several things needed to define the thread's behaviour.

        Args:
            interface (str): The network interface which should be used. (e.g. eth0)
            gateway (str): IP address of the gateway.
            mac (str): MAC address of the spoofing device. (own MAC address)
            gate_mac (str): MAC address of the gateway.

        """
        threading.Thread.__init__(self)
        self.interface = interface
        self.ipv4 = ipv4
        self.ipv6 = ipv6

        # deprecated
        # self.gateway = self.ipv4.gateway
        # self.mac = self.ipv4.mac
        # self.gate_mac = self.ipv4.gate_mac

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

    def __init__(self, interface, ipv4, ipv6):
        """Initialises several things needed to define the thread's behaviour.

        Args:
            interface (str): The network interface which should be used. (e.g. eth0)
            gateway (str): IP address of the gateway.
            mac (str): MAC address of the spoofing device. (own MAC address)
            gate_mac (str): MAC address of the gateway.

        """
        super(self.__class__, self).__init__(interface, ipv4, ipv6)

    def _packet_handler(self, pkt):
        """This method is called for each packet received through scapy's sniff function.
        Incoming ARP requests are used to spoof involved devices.

        Args:
            pkt (str): Received packet via scapy's sniff (through socket.recv).
        """
        # when ARP request
        if pkt[ARP].op == 1:

            # packets intended for this machine (upribox)
            if pkt[Ether].dst == self.ipv4.mac:
                # incoming packets(that are sniffed): Windows correctly fills in the hwdst, linux (router) only 00:00:00:00:00:00
                # this answers packets asking if we are the gateway (directly not via broadcast)
                # Windows does this 3 times before sending a broadcast request
                sendp(Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwdst=pkt[ARP].hwsrc, hwsrc=self.ipv4.mac))

            # broadcast request to gateway
            elif pkt[Ether].dst.lower() == util.hex2str_mac(ETHER_BROADCAST) and (pkt[ARP].pdst == self.ipv4.gateway):
                # pkt[ARP].psrc == self.gateway or

                # spoof transmitter
                packets = [Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwsrc=self.ipv4.mac, hwdst=pkt[ARP].hwsrc)]

                # # get mac address of original target
                # dest = self.gate_mac
                # if pkt[ARP].pdst != self.gateway:
                #     # send arp request if destination was not the gateway
                #     dest = util.get_mac(pkt[ARP].pdst, self.interface)
                #
                # if dest:
                #     # spoof receiver
                #     packets.append(Ether(dst=dest) / ARP(op=2, psrc=pkt[ARP].psrc, hwsrc=self.mac, pdst=pkt[ARP].pdst, hwdst=dest))

                # some os didn't accept an answer immediately (after sending the first ARP request after boot
                # so, send packets after some delay
                threading.Timer(self._DELAY, sendp, [packets]).start()
                # TODO gratuitous neighbor advertisements


class SelectiveSniffThread(_SniffThread):
    """Implements the abstract class _SniffThread and also implements
    the listener of the selective spoofing mode of Apate.
    """

    _SNIFF_FILTER = "(arp or igmp or (icmp6 and ip6[40] == 129) or (multicast and ip6[48] == 131) or (icmp6 and ip6[40] == 134)) and inbound"
    """str: tcpdump filter used for scapy's sniff function."""
    _LFILTER = staticmethod(lambda x: any([x.haslayer(layer) for layer in (ARP, IGMP, ICMPv6EchoReply, ICMPv6MLReport)]))
    """function: lambda filter used for scapy's sniff function."""

    def __init__(self, interface, ipv4, ipv6, sleeper):
        """Initialises several things needed to define the thread's behaviour.

        Args:
            interface (str): The network interface which should be used. (e.g. eth0)
            gateway (str): IP address of the gateway.
            mac (str): MAC address of the spoofing device. (own MAC address)
            gate_mac (str): MAC address of the gateway.
            redis (apate_redis.ApateRedis): Used to add new devices to redis db.

        """
        super(self.__class__, self).__init__(interface, ipv4, ipv6)
        self.sleeper = sleeper

    def _packet_handler(self, pkt):
        """This method is called for each packet received through scapy's sniff function.

        Args:
            pkt (str): Received packet via scapy's sniff (through socket.recv).
        """

        if self.ipv4 and pkt.haslayer(ARP):
            self._arp_handler(pkt)
        elif self.ipv4 and pkt.haslayer(IGMP):
            self._igmp_handler(pkt)
        if self.ipv6 and pkt.haslayer(ICMPv6EchoReply) and pkt[ICMPv6EchoReply].data == MulticastPingDiscoveryThread._DATA:
            self._icmpv6_handler(pkt)
        elif self.ipv6 and pkt.haslayer(ICMPv6MLReport):
            self._icmpv6_handler(pkt)
        elif self.ipv6 and pkt.haslayer(ICMPv6ND_RA):
            with self.sleeper:
                self.sleeper.notifyAll()

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
            if pkt[Ether].dst == self.ipv4.mac:
                # incoming packets(that are sniffed): Windows correctly fills in the hwdst, linux (router) only 00:00:00:00:00:00
                # this answers packets asking if we are the gateway (directly not via broadcast)
                # Windows does this 3 times before sending a broadcast request
                sendp(Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwdst=pkt[ARP].hwsrc, hwsrc=self.ipv4.mac))
                # add transmitting device to redis db
                self.ipv4.redis.add_device(pkt[ARP].psrc, pkt[ARP].hwsrc)

            # broadcast request to gateway
            elif pkt[Ether].dst.lower() == util.hex2str_mac(ETHER_BROADCAST) and (pkt[ARP].pdst == self.ipv4.gateway):
                    # pkt[ARP].psrc == self.gateway or

                    # spoof transmitter
                packets = [Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwsrc=self.ipv4.mac, hwdst=pkt[ARP].hwsrc)]

                # # get mac address of original target
                # dest = self.gate_mac
                # if pkt[ARP].pdst != self.gateway:
                #     # send arp request if destination was not the gateway
                #     dest = util.get_mac(pkt[ARP].pdst, self.interface)
                #
                # if dest:
                #     # spoof receiver
                #     packets.append(Ether(dst=dest) / ARP(op=2, psrc=pkt[ARP].psrc, hwsrc=self.mac, pdst=pkt[ARP].pdst, hwdst=dest))

                # add transmitting device to redis db
                self.ipv4.redis.add_device(pkt[ARP].psrc, pkt[ARP].hwsrc)
                # add receiving device to redis db
                # self.redis.add_device(pkt[ARP].pdst, dest)

                # some os didn't accept an answer immediately (after sending the first ARP request after boot
                # so, send packets after some delay
                threading.Timer(self._DELAY, sendp, [packets]).start()
        else:
                # ARP reply
                # add transmitting device to redis db
            self.ipv4.redis.add_device(pkt[ARP].psrc, pkt[ARP].hwsrc)

    def _igmp_handler(self, pkt):
        """"This method is called for each IGMP packet received through scapy's sniff function.
        Incoming IGMP answers are used to spoof involved devices and add new devices
        to the redis db.

        Args:
            pkt (str): Received packet via scapy's sniff (through socket.recv).
        """
        # if util.get_mac(pkt[IP].src,self.interface):
        self.ipv4.redis.add_device(pkt[IP].src, pkt[Ether].src)
        sendp(Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=self.ipv4.gateway, pdst=pkt[IP].src, hwdst=pkt[Ether].src))
        # sendp([Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=self.gateway, pdst=pkt[IP].src, hwdst=pkt[Ether].src),
        #        Ether(dst=self.gate_mac) / ARP(op=2, psrc=pkt[IP].src, pdst=self.gateway, hwdst=self.gate_mac)])

    def _icmpv6_handler(self, pkt):
        """"This method is called for each IGMP packet received through scapy's sniff function.
        Incoming IGMP answers are used to spoof involved devices and add new devices
        to the redis db.

        Args:
            pkt (str): Received packet via scapy's sniff (through socket.recv).
        """
        # if util.get_mac(pkt[IP].src,self.interface):

        self.ipv6.redis.add_device(pkt[IPv6].src, pkt[Ether].src)
        sendp(Ether(dst=pkt[Ether].src) / IPv6(src=self.ipv6.gateway, dst=pkt[IPv6].src) /
              ICMPv6ND_NA(tgt=self.ipv6.gateway, R=0, S=1) / ICMPv6NDOptDstLLAddr(lladdr=self.ipv6.mac))
        # sendp(Esther(dst=pkt[Ether].src) / ARP(op=2, psrc=self.gateway, pdst=pkt[IP].src, hwdst=pkt[Ether].src))
        if util.is_spoof_dns(self.ipv6):
            sendp(Ether(dst=pkt[Ether].src) / IPv6(src=self.ipv6.dns_servers[0], dst=pkt[IPv6].src) /
                  ICMPv6ND_NA(tgt=self.ipv6.dns_servers[0], R=0, S=1) / ICMPv6NDOptDstLLAddr(lladdr=self.ipv6.mac))
