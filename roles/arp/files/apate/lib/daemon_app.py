# import sys
import os
# import thread
import logging
import time
import netifaces as ni
import threading
# import socket
# import struct
# import binascii

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import conf, sendp, srp, ARP, Ether, ETHER_BROADCAST, sniff
from netaddr import IPAddress, IPNetwork, AddrFormatError

import util
from sniff_thread import HolisticSniffThread, SelectiveSniffThread
from apate_redis import ApateRedis


class _DaemonApp(object):

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

    def __return_to_normal(self):
        pass

    def exit(self, signal_number, stack_frame):
        self.__return_to_normal()
        # TODO check if thread is alive (active)
        # self.t1.stop()
        raise SystemExit()

    def run(self):
        pass


class HolisticDaemonApp(_DaemonApp):

    def __init__(self, logger, interface, pidfile, stdout, stderr):
        super(self.__class__, self).__init__(logger, interface, pidfile, stdout, stderr)

        self.t1 = HolisticSniffThread(self.interface, self.gateway, self.mac, self.gateMAC)
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


class SelectiveDaemonApp(_DaemonApp):

    def __init__(self, logger, interface, pidfile, stdout, stderr):
        super(self.__class__, self).__init__(logger, interface, pidfile, stdout, stderr)
        self.redis = ApateRedis(self.network, logger)

        # TODO change
        # self.t1 = HolisticSniffThread(self.interface, self.gateway, self.mac, self.gateMAC)
        # self.t1.daemon = True
        self.t1 = SelectiveSniffThread(self.interface, self.gateway, self.mac, self.gateMAC, self.redis)
        self.t1.daemon = True

    def __return_to_normal(self):

        # spoof clients
        sendp(
            Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.gateway, hwdst=ETHER_BROADCAST,
                                             hwsrc=self.gateMAC))

        # packets = [Ether(dst=dev[1]) / ARP(op=1, psrc=self.gateway, pdst=dev[0].rsplit(":", 1)[-1], hwsrc=self.gateMAC) for dev in self.redis.get_devices_values(filter=True)]

        # spoof the gateway
        packets = [Ether(dst=self.gateMAC) / ARP(op=2, psrc=dev[0], pdst=self.gateway, hwsrc=dev[1]) for dev in self.redis.get_devices_values(filter=True)]

        sendp(packets)

    def exit(self, signal_number, stack_frame):
        self.__return_to_normal()
        # TODO check if thread is alive (active)
        self.t1.stop()
        raise SystemExit()

    def run(self):
        # TODO
        # start threads (listener and host discovery)
        # TODO sleep for redis pubsub
        # time.sleep(3)
        self.t1.start()

        DiscoveryThread(self.gateway, self.network).start()

        # spoof clients
        p1 = lambda dev: Ether(dst=dev[1]) / ARP(op=2, psrc=self.gateway, pdst=dev[0], hwdst=dev[1])

        # spoof gateway
        p2 = lambda dev: Ether(dst=self.gateMAC) / ARP(op=2, psrc=dev[0], pdst=self.gateway, hwdst=self.gateMAC)

        while(True):
            packets = [p(dev) for dev in self.redis.get_devices_values(filter=True) for p in (p1, p2)]

            # # spoof clients
            # packets = [Ether(dst=dev[1]) / ARP(op=2, psrc=self.gateway, pdst=util.get_device_ip(dev[0]), hwdst=dev[1]) for dev in self.redis.get_devices_values(filter=True)]
            #
            # # spoof gateway
            # packets += [Ether(dst=self.gateMAC) / ARP(op=2, psrc=util.get_device_ip(dev[0], pdst=self.gateway, hwdst=self.gateMAC)) for dev in]

            sendp(packets)
            time.sleep(5)


class DaemonError(Exception):
    pass


class DiscoveryThread(threading.Thread):

    def __init__(self, gateway, network):
        threading.Thread.__init__(self)
        # super(self.__class__, self).__init__()
        # self.interface = interface
        self.gateway = gateway
        self.network = network
        # self.mac = mac
        # self.gateMAC = gateMAC

    def run(self):
        sendp(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=str(self.network)))

    def stop(self):
        thread.exit()
