import thread
import logging
import threading

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import conf, sendp, srp, ARP, Ether, ETHER_BROADCAST, sniff

import util


class _SniffThread(threading.Thread):

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
        sniff(prn=self._arp_handler, filter="arp and inbound", lfilter=lambda x: x.haslayer(ARP), store=0, iface=self.interface)

    def _arp_handler(self, pkt):
        pass

    def stop(self):
        thread.exit()


class HolisticSniffThread(_SniffThread):

    def __init__(self, interface, gateway, mac, gateMAC):
        super(self.__class__, self).__init__(interface, gateway, mac, gateMAC)

    def _arp_handler(self, pkt):
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


class SelectiveSniffThread(_SniffThread):

    def __init__(self, interface, gateway, mac, gateMAC, redis):
        super(self.__class__, self).__init__(interface, gateway, mac, gateMAC)
        self.redis = redis

    def _arp_handler(self, pkt):
        if pkt[ARP].op == 1:
            if pkt[Ether].dst == self.mac:
                # incoming packets(that are sniffed): Windows correctly fills in the hwdst, linux (router) only 00:00:00:00:00:00
                sendp(Ether(dst=pkt[Ether].src) / ARP(op=2, psrc=pkt[ARP].pdst, pdst=pkt[ARP].psrc, hwdst=pkt[ARP].hwsrc, hwsrc=self.mac))
                # TODO also spoof gateway?
                # TODO not needed, if perfomance is not sufficient
                self.redis.add_device(pkt[ARP].psrc, pkt[ARP].hwsrc)

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

                self.redis.add_device(pkt[ARP].psrc, pkt[ARP].hwsrc)
                self.redis.add_device(pkt[ARP].pdst, dest)
                # print packets[0].show()
                # print packets[1].show()

                threading.Timer(7.0, sendp, [packets]).start()
        else:
            # ARP reply
            self.redis.add_device(pkt[ARP].psrc, pkt[ARP].hwsrc)
