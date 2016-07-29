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
from scapy.all import sendp, ARP, Ether, IP, ETHER_BROADCAST, sniff
from scapy.contrib.igmp import IGMP

import util


class _SniffThread(threading.Thread):
    """This is an abstract class, which should be inherited to define the
    behaviour fo the sniffing thread."""

    _DELAY = 7.0
    """float: Delay after which packets are sent."""
    _SNIFF_FILTER = "arp and inbound"
    """str: tcpdump filter used for scapy's sniff function."""
    _LFILTER = staticmethod(lambda x: x.haslayer(ARP))
    """function: lambda filter used for scapy's sniff function."""

    def __init__(self, interface, gateway, mac, gate_mac):
        """Initialises several things needed to define the thread's behaviour.

        Args:
            interface (str): The network interface which should be used. (e.g. eth0)
            gateway (str): IP address of the gateway.
            mac (str): MAC address of the spoofing device. (own MAC address)
            gate_mac (str): MAC address of the gateway.

        """
        threading.Thread.__init__(self)
        self.interface = interface
        self.gateway = gateway
        self.mac = mac
        self.gate_mac = gate_mac

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

    def __init__(self, interface, gateway, mac, gate_mac):
        """Initialises several things needed to define the thread's behaviour.

        Args:
            interface (str): The network interface which should be used. (e.g. eth0)
            gateway (str): IP address of the gateway.
            mac (str): MAC address of the spoofing device. (own MAC address)
            gate_mac (str): MAC address of the gateway.

        """
        super(self.__class__, self).__init__(interface, gateway, mac, gate_mac)

    def _packet_handler(self, pkt):
        """This method is called for each packet received through scapy's sniff function.
        Incoming ARP requests are used to spoof involved devices.

        Args:
            pkt (str): Received packet via scapy's sniff (through socket.recv).
        """
        # when ARP request
        if pkt[ARP].op == 1:

            # packets intended for this machine (upribox)
            if pkt[Ether].dst == self.mac:
                # incoming packets(that are sniffed): Windows correctly fills in the hwdst, linux (router) only 00:00:00:00:00:00
                # this answers packets asking if we are the gateway (directly not via broadcast)
                # Windows does this 3 times before sending a broadcast request
                sendp(Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwdst=pkt[ARP].hwsrc, hwsrc=self.mac))

            # broadcast request to or from gateway
            elif pkt[Ether].dst.lower() == util.hex2str_mac(ETHER_BROADCAST) and (pkt[ARP].psrc == self.gateway or pkt[ARP].pdst == self.gateway):
                # spoof transmitter
                packets = [Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwsrc=self.mac, hwdst=pkt[ARP].hwsrc)]

                # get mac address of original target
                dest = self.gate_mac
                if pkt[ARP].pdst != self.gateway:
                    # send arp request if destination was not the gateway
                    dest = util.get_mac(pkt[ARP].pdst, self.interface)

                if dest:
                    # spoof receiver
                    packets.append(Ether(dst=dest) / ARP(op=2, psrc=pkt[ARP].psrc, hwsrc=self.mac, pdst=pkt[ARP].pdst, hwdst=dest))

                # some os didn't accept an answer immediately (after sending the first ARP request after boot
                # so, send packets after some delay
                threading.Timer(self._DELAY, sendp, [packets]).start()


class SelectiveSniffThread(_SniffThread):
    """Implements the abstract class _SniffThread and also implements
    the listener of the selective spoofing mode of Apate.
    """

    _SNIFF_FILTER = "(arp or igmp) and inbound"
    """str: tcpdump filter used for scapy's sniff function."""
    _LFILTER = staticmethod(lambda x: any([x.haslayer(layer) for layer in (ARP, IGMP)]))
    """function: lambda filter used for scapy's sniff function."""

    def __init__(self, interface, gateway, mac, gate_mac, redis):
        """Initialises several things needed to define the thread's behaviour.

        Args:
            interface (str): The network interface which should be used. (e.g. eth0)
            gateway (str): IP address of the gateway.
            mac (str): MAC address of the spoofing device. (own MAC address)
            gate_mac (str): MAC address of the gateway.
            redis (apate_redis.ApateRedis): Used to add new devices to redis db.

        """
        super(self.__class__, self).__init__(interface, gateway, mac, gate_mac)
        self.redis = redis

    def _packet_handler(self, pkt):
        """This method is called for each packet received through scapy's sniff function.

        Args:
            pkt (str): Received packet via scapy's sniff (through socket.recv).
        """

        if pkt.haslayer(ARP):
            self._arp_handler(pkt)
        elif pkt.haslayer(IGMP):
            self._igmp_handler(pkt)

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
            if pkt[Ether].dst == self.mac:
                # incoming packets(that are sniffed): Windows correctly fills in the hwdst, linux (router) only 00:00:00:00:00:00
                # this answers packets asking if we are the gateway (directly not via broadcast)
                # Windows does this 3 times before sending a broadcast request
                sendp(Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwdst=pkt[ARP].hwsrc, hwsrc=self.mac))
                # add transmitting device to redis db
                self.redis.add_device(pkt[ARP].psrc, pkt[ARP].hwsrc)

            # broadcast request to or from gateway
            elif pkt[Ether].dst.lower() == util.hex2str_mac(ETHER_BROADCAST) and (pkt[ARP].psrc == self.gateway or pkt[ARP].pdst == self.gateway):
                # spoof transmitter
                packets = [Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwsrc=self.mac, hwdst=pkt[ARP].hwsrc)]

                # get mac address of original target
                dest = self.gate_mac
                if pkt[ARP].pdst != self.gateway:
                    # send arp request if destination was not the gateway
                    dest = util.get_mac(pkt[ARP].pdst, self.interface)

                if dest:
                    # spoof receiver
                    packets.append(Ether(dst=dest) / ARP(op=2, psrc=pkt[ARP].psrc, hwsrc=self.mac, pdst=pkt[ARP].pdst, hwdst=dest))

                # add transmitting device to redis db
                self.redis.add_device(pkt[ARP].psrc, pkt[ARP].hwsrc)
                # add receiving device to redis db
                self.redis.add_device(pkt[ARP].pdst, dest)

                # some os didn't accept an answer immediately (after sending the first ARP request after boot
                # so, send packets after some delay
                threading.Timer(self._DELAY, sendp, [packets]).start()
        else:
            # ARP reply
            # add transmitting device to redis db
            self.redis.add_device(pkt[ARP].psrc, pkt[ARP].hwsrc)

    def _igmp_handler(self, pkt):
        """"This method is called for each IGMP packet received through scapy's sniff function.
        Incoming IGMP answers are used to spoof involved devices and add new devices
        to the redis db.

        Args:
            pkt (str): Received packet via scapy's sniff (through socket.recv).
        """
        # if util.get_mac(pkt[IP].src,self.interface):
        self.redis.add_device(pkt[IP].src, pkt[Ether].src)
        sendp([Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=self.gateway, pdst=pkt[IP].src, hwdst=pkt[Ether].src),
               Ether(dst=self.gate_mac) / ARP(op=2, psrc=pkt[IP].src, pdst=self.gateway, hwdst=self.gate_mac)])
