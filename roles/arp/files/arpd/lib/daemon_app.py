import sys
import os
import thread
import logging
import time
import netifaces as ni
import threading

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import conf, sendp, srp, ARP, Ether, ETHER_BROADCAST, sniff
from netaddr import IPAddress, IPNetwork, AddrFormatError


class DaemonApp():
    def __init__(self, logger, interface):
        # disable scapys verbosity global
        conf.verb = 0

        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = '/var/run/arpd/arpd.pid'
        self.pidfile_timeout = 5
        # self.pidfile_timeout = 0

        self.logger = logger
        self.interface = interface

        if_info = None
        try:
            if_info = ni.ifaddresses(self.interface)
            # self.ip = ni.ifaddresses(self.interface)[2][0]['addr']
        except ValueError as e:
            self.logger.error("An error concerning the interface %s has occurred: %s" % (self.interface, str(e)))
            raise DaemonException()

        # get ip of specified interface
        self.ip = if_info[2][0]['addr']
        # get subnetmask of specified interface
        self.netmask = if_info[2][0]['netmask']

        # get network address
        try:
            self.network = IPNetwork("%s/%s" % (self.ip, self.netmask))
        except AddrFormatError as afe:
            # this should never happen, because values are retrieved via netifaces library
            self.logger.error("A grave error happened during determinig the network: %s" % str(afe))
            raise DaemonException()

        # get default gateway
        try:
            self.gateway = ni.gateways()["default"][ni.AF_INET][0]
        except KeyError:
            self.logger.error("No default gateway is configured")
            raise DaemonException()

        # get all ip addresses that are in the specified network
        # and remove network address, broadcast, own ip, gateway ip
        self.ip_range = list(self.network)
        self.ip_range.remove(IPAddress(self.ip))
        self.ip_range.remove(IPAddress(self.gateway))
        self.ip_range.remove(IPAddress(self.network.broadcast))
        self.ip_range.remove(IPAddress(self.network.network))

        try:
            # get MAC address of gateway
            self.gateMAC = self.__get_mac(self.gateway)
        except Exception:
            self.logger.error("Unable to get MAC address of Gateway")
            raise DaemonException()
            # print "[!] Couldn't Find Gateway MAC Address"
            # print "[!] Exiting..."
            # sys.exit(1)

        self.t1 = SniffThread(self.interface, self.gateway)
        self.t1.daemon = True

    def __get_mac(self, ip):
        ans, unans = srp(Ether(dst=ETHER_BROADCAST) / ARP(pdst=ip), timeout=2, iface=self.interface, inter=0.1)
        for snd, rcv in ans:
            return rcv.sprintf(r"%Ether.src%")

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
        # t1 = SniffThread(self.interface, self.gateway)
        # t1.daemon = True
        self.t1.start()

        # generate packets to send to gateway
        packets = [Ether(dst=self.gateMAC) / ARP(op=1, psrc=str(x), pdst=self.gateway) for x in self.ip_range]

        while True:
            # gratuitous arp to clients
            sendp(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.gateway,
                                                   hwdst=ETHER_BROADCAST))

            # trick gateway
            # sendp(Ether(dst=self.gateMAC) / ARP(op=1, psrc=str(self.network), pdst=self.gateway))
            sendp(packets)
            time.sleep(20)


class SniffThread(threading.Thread):  # Process):
    def __init__(self, interface, gateway):
        threading.Thread.__init__(self)
        # super(self.__class__, self).__init__()
        self.interface = interface
        self.gateway = gateway

    def run(self):
        sniff(prn=self.__arp_handler, lfilter=lambda x: x.haslayer(ARP), store=0, iface=self.interface)

    def __arp_handler(self, pkt):
        #    if pkt.haslayer(ARP):
        if pkt[ARP].op == 1:
            if pkt[ARP].pdst == self.gateway:
                sendp(Ether(dst=pkt[ARP].hwsrc) / ARP(op=2, psrc=self.gateway, hwdst=pkt[ARP].hwsrc,
                                                      pdst=pkt[ARP].psrc))
            elif pkt[ARP].psrc == self.gateway:
                sendp(
                    Ether(dst=pkt[ARP].hwsrc) / ARP(op=2, psrc=pkt[ARP].pdst, hwdst=pkt[ARP].hwsrc, pdst=pkt[ARP].psrc))

    def stop(self):
        thread.exit()


class DaemonException(Exception):
    pass
