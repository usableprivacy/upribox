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

    def __init__(self, logger, interface, pidfile):
        # disable scapys verbosity global
        conf.verb = 0

        self.stdin_path = os.devnull #'/dev/null'
        self.stdout_path = '/var/log/log/apate/std.log' #os.ttyname(sys.stdout.fileno()) #'/dev/tty'#'/var/log/log/apate/apate.log'#
        self.stderr_path = '/var/log/log/apate/std.log' #os.ttyname(sys.stderr.fileno()) #'/dev/tty'#'/var/log/log/apate/apate.log'#
        self.pidfile_path = pidfile
        self.pidfile_timeout = 5
        # self.pidfile_timeout = 0

        self.logger = logger
        self.interface = interface

        if_info = None
        try:
            if_info = ni.ifaddresses(self.interface)
            # self.ip = ni.ifaddresses(self.interface)[2][0]['addr']
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
            self.gateMAC = util.get_mac(self.gateway, self.interface) #self.__get_mac(self.gateway)
        except Exception:
            self.logger.error("Unable to get MAC address of Gateway")
            raise DaemonError()
            # print "[!] Couldn't Find Gateway MAC Address"
            # print "[!] Exiting..."
            # sys.exit(1)

        self.t1 = SniffThread(self.interface, self.gateway, self.mac, self.gateMAC)
        self.t1.daemon = True

    # def __get_mac(self, ip):
    #     ans, unans = srp(Ether(dst=ETHER_BROADCAST) / ARP(pdst=ip), timeout=2, iface=self.interface, inter=0.1)
    #     for snd, rcv in ans:
    #         return rcv.sprintf(r"%Ether.src%")

    def __return_to_normal(self):
        # clients gratutious arp
        sendp(
            Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.gateway, hwdst=ETHER_BROADCAST,
                                             hwsrc=self.gateMAC))
        # to clients so that they send and arp reply to the gateway
        sendp(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=str(self.network), hwsrc=self.gateMAC))

    def exit(self, signal_number, stack_frame):
        self.t1.stop()
        self.__return_to_normal()
        # TODO check if thread is alive (active)
        # self.t1.stop()
        raise SystemExit()

    def run(self):
        # start sniffing thread
        # t1 = SniffThread(self.interface, self.gateway)
        # t1.daemon = True
        self.t1.start()

        # generate packets to send to gateway
        # this tells the gateway that the upribox is every client ip
        # packets = [Ether(dst=self.gateMAC) / ARP(op=1, psrc=str(x), pdst=self.gateway) for x in self.ip_range]

        # TODO maybe change oder?
        # this updates entries in the arp table of the gateway
        packets = [Ether(dst=self.gateMAC) / ARP(op=1, psrc=str(x), pdst=str(x)) for x in self.ip_range]
        # gratuitous arp to clients
        packets.append(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.gateway,
                                               hwdst=ETHER_BROADCAST))
        while True:
            # gratuitous arp to clients
            # sendp(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.gateway,
            #                                        hwdst=ETHER_BROADCAST))

            # trick gateway
            # sendp(Ether(dst=self.gateMAC) / ARP(op=1, psrc=str(self.network), pdst=self.gateway))
            sendp(packets)
            # increasing this value shouldn't be a problem
            time.sleep(20)


class SniffThread(threading.Thread):  # Process):

    def __init__(self, interface, gateway, mac, gateMAC):
        threading.Thread.__init__(self)
        # super(self.__class__, self).__init__()
        self.interface = interface
        self.gateway = gateway
        self.mac = mac
        self.gateMAC = gateMAC

    def run(self):
        # rawSocket = socket.socket(socket.PF_PACKET, socket.SOCK_RAW, socket.htons(0x0806))
        # #rawSocket = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(0x0003))
        #
        # while True:
        #
        #     packet = rawSocket.recvfrom(2048)
        #
        #     ethernet_header = packet[0][0:14]
        #     ethernet_detailed = struct.unpack("!6s6s2s", ethernet_header)
        #
        #     arp_header = packet[0][14:42]
        #     arp_detailed = struct.unpack("2s2s1s1s2s6s4s6s4s", arp_header)
        #
        #     # skip non-ARP packets
        #     #ethertype = ethernet_detailed[2]
        #     # if ethertype != '\x08\x06':
        #     #    continue
        #
        #     # print ARP(str(packet)).show()
        #
        #     pkt = ARP(str(packet))
        #
        #     if pkt[ARP].op == 1:
        #         if pkt[ARP].pdst == self.gateway:
        #             sendp(Ether(dst=pkt[ARP].hwsrc) / ARP(op=2, psrc=self.gateway, hwdst=pkt[ARP].hwsrc,
        #                                                   pdst=pkt[ARP].psrc))
        #             print "case 1"
        #         elif pkt[ARP].psrc == self.gateway:
        #             sendp(
        #                 Ether(dst=pkt[ARP].hwsrc) / ARP(op=2, psrc=pkt[ARP].pdst, hwdst=pkt[ARP].hwsrc, pdst=pkt[ARP].psrc))
        #             print "case 2"

        #  --------------------------------------------------------------------------------

        # the filter argument in scapy's sniff function seems to be applied too late
        # therefore some unwanted packets are processed (e.g. tcp packets of ssh session)
        # but it still decreases the number of packets that need to be processed by the lfilter function
        sniff(prn=self.__arp_handler, filter="arp and inbound", lfilter=lambda x: x.haslayer(ARP), store=0, iface=self.interface)

    def __arp_handler(self, pkt):
        #    if pkt.haslayer(ARP):
        # print pkt.show()
        if pkt[ARP].op == 1:

            if pkt[Ether].dst == self.mac:
                #incoming packets(that are sniffed): Windows correctly fills in the hwdst, linux (router) only 00:00:00:00:00:00
                sendp(Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwdst=pkt[ARP].hwsrc, hwsrc=self.mac))

            # broadcast request to or from gateway
            elif pkt[Ether].dst.lower() == util.hex2str_mac(ETHER_BROADCAST) and (pkt[ARP].psrc == self.gateway or pkt[ARP].pdst == self.gateway):
                print "entered"
                # spoof transmitter
                packets = [Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwsrc=self.mac, hwdst=pkt[ARP].hwsrc)]
                # spoof receiver
                dest = self.gateMAC
                if pkt[ARP].pdst != self.gateway:
                    dest = util.get_mac(pkt[ARP].pdst, self.interface)#__get_mac(pkt[ARP].pdst)

                packets.append(Ether(dst=dest) / ARP(op=2, psrc=pkt[ARP].psrc, hwsrc=self.mac, pdst=pkt[ARP].pdst, hwdst=dest))

                # packets = [Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=pkt[ARP].pdst, pdst=pkt[ARP].pdst, hwdst=ETHER_BROADCAST)]
                # packets.append(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=pkt[ARP].psrc, pdst=pkt[ARP].psrc, hwdst=ETHER_BROADCAST))

                print packets[0].show()
                print packets[1].show()

                threading.Timer(7.0, sendp, [packets]).start()

                # sendp(packets)

            # print "%s -> %s" % (pkt[Ether].src, pkt[Ether].dst)

            # desired cases
            # if pkt[Ether].dst == ETHER_BROADCAST and pkt[Ether].src != self.mac:
            #     pass
            #
            # elif pkt[ARP].pdst == self.gateway and pkt[ARP].hwdst == self.mac:
            #     # e.g. NB3 asks raspberry if it is the gateway
            #     sendp(Ether(dst=pkt[ARP].hwsrc) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwdst=pkt[ARP].hwsrc, hwsrc=pkt[ARP].hwdst))
            #     print "new case 1"
            #     print pkt.show()

        #     # TODO HWSOURCE
        #     if pkt[ARP].pdst == self.gateway and pkt[ARP].hwsrc != self.mac:
        #         # if someone asks for the gateway
        #         # for i in range(3):
        #         #     # trick client
        #         #     sendp(Ether(dst=pkt[ARP].hwsrc) / ARP(op=2, psrc=self.gateway, hwdst=pkt[ARP].hwsrc,
        #         #                                           pdst=pkt[ARP].psrc))
        #         #     # trick gateway
        #         #     sendp(Ether(dst=pkt[ARP].gateMAC) / ARP(op=1, psrc=pkt[ARP].psrc, pdst=pkt[ARP].pdst))
        #         print "old case 1"
        #         print pkt.show()
        #
        #     # TODO Here ALSO
        # elif pkt[ARP].psrc == self.gateway and pkt[ARP].hwsrc == self.gateMAC:
        #         # if gateway asks for someone
        #         # trick gateway
        #         # for i in range(3):
        #         #     sendp(
        #         #         Ether(dst=pkt[ARP].hwsrc) / ARP(op=2, psrc=pkt[ARP].pdst, hwdst=pkt[ARP].hwsrc, pdst=pkt[ARP].psrc))
        #         #     # tricks client (also new client)
        #         #     sendp(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.gateway,
        #         #                                            hwdst=ETHER_BROADCAST))
        #     print "old case 2"
        #     print pkt.show()

    # def __get_mac(self, ip):
    #     ans, unans = srp(Ether(dst=ETHER_BROADCAST) / ARP(pdst=ip), timeout=2, iface=self.interface, inter=0.1)
    #     for snd, rcv in ans:
    #         return rcv.sprintf(r"%Ether.src%")

    def stop(self):
        thread.exit()


class DaemonError(Exception):
    pass
