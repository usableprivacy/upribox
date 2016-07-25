import os
import thread
import logging
import time
import threading
import netifaces as ni
from netaddr import IPAddress, IPNetwork, AddrFormatError

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import conf, sendp, ARP, Ether, ETHER_BROADCAST

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
            self.gate_mac = util.get_mac(self.gateway, self.interface)
        except Exception:
            self.logger.error("Unable to get MAC address of Gateway")
            raise DaemonError()

    def __return_to_normal(self):
        pass

    def exit(self, signal_number, stack_frame):
        self.__return_to_normal()
        # TODO check if thread is alive (active)
        # self.sniffthread.stop()
        raise SystemExit()

    def run(self):
        pass


class HolisticDaemonApp(_DaemonApp):

    def __init__(self, logger, interface, pidfile, stdout, stderr):
        super(self.__class__, self).__init__(logger, interface, pidfile, stdout, stderr)

        self.sniffthread = HolisticSniffThread(self.interface, self.gateway, self.mac, self.gate_mac)
        self.sniffthread.daemon = True

    def __return_to_normal(self):
        # clients gratutious arp
        sendp(
            Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.gateway, hwdst=ETHER_BROADCAST,
                                             hwsrc=self.gate_mac))
        # to clients so that they send and arp reply to the gateway
        sendp(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=str(self.network), hwsrc=self.gate_mac))

    def exit(self, signal_number, stack_frame):
        self.__return_to_normal()
        # TODO check if thread is alive (active)
        self.sniffthread.stop()
        raise SystemExit()

    def run(self):
        # start sniffing thread
        self.sniffthread.start()

        # this updates existing entries in the arp table of the gateway
        packets = [Ether(dst=self.gate_mac) / ARP(op=1, psrc=str(x), pdst=str(x)) for x in self.ip_range]
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

        self.sniffthread = SelectiveSniffThread(self.interface, self.gateway, self.mac, self.gate_mac, self.redis)
        self.sniffthread.daemon = True
        self.psthread = PubSubThread(self.redis, self.logger)
        self.psthread.daemon = True
        self.dt = DiscoveryThread(self.gateway, self.network)
        self.dt.daemon = True

    def __return_to_normal(self):

        # spoof clients
        sendp(
            Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=self.gateway, hwdst=ETHER_BROADCAST,
                                             hwsrc=self.gate_mac))

        # packets = [Ether(dst=dev[1]) / ARP(op=1, psrc=self.gateway, pdst=dev[0].rsplit(":", 1)[-1], hwsrc=self.gate_mac) for dev in self.redis.get_devices_values(filter=True)]

        # spoof the gateway
        packets = [Ether(dst=self.gate_mac) / ARP(op=2, psrc=dev[0], pdst=self.gateway, hwsrc=dev[1]) for dev in self.redis.get_devices_values(filter_values=True)]

        sendp(packets)

    def exit(self, signal_number, stack_frame):
        self.__return_to_normal()
        # TODO check if thread is alive (active)
        self.sniffthread.stop()
        self.psthread.stop()
        raise SystemExit()

    def run(self):
        self.sniffthread.start()
        self.dt.start()
        self.psthread.start()

        # spoof clients
        p1 = lambda dev: Ether(dst=dev[1]) / ARP(op=2, psrc=self.gateway, pdst=dev[0], hwdst=dev[1])

        # spoof gateway
        p2 = lambda dev: Ether(dst=self.gate_mac) / ARP(op=2, psrc=dev[0], pdst=self.gateway, hwdst=self.gate_mac)

        while True:
            packets = [p(dev) for dev in self.redis.get_devices_values(filter_values=True) for p in (p1, p2)]

            # # spoof clients
            # packets = [Ether(dst=dev[1]) / ARP(op=2, psrc=self.gateway, pdst=util.get_device_ip(dev[0]), hwdst=dev[1]) for dev in self.redis.get_devices_values(filter=True)]
            #
            # # spoof gateway
            # packets += [Ether(dst=self.gate_mac) / ARP(op=2, psrc=util.get_device_ip(dev[0], pdst=self.gateway, hwdst=self.gate_mac)) for dev in]

            sendp(packets)
            time.sleep(5)


class DaemonError(Exception):
    pass


class DiscoveryThread(threading.Thread):

    def __init__(self, gateway, network):
        threading.Thread.__init__(self)
        # super(self.__class__, self).__init__()
        self.gateway = gateway
        self.network = network

    def run(self):
        sendp(Ether(dst=ETHER_BROADCAST) / ARP(op=1, psrc=self.gateway, pdst=str(self.network)))

    @staticmethod
    def stop():
        thread.exit()


class PubSubThread(threading.Thread):

    def __init__(self, redis, logger):
        threading.Thread.__init__(self)
        # super(self.__class__, self).__init__()
        self.redis = redis
        self.logger = logger

    def run(self):
        p = self.redis.get_pubsub()
        p.subscribe("__keyevent@5__:expired")  # **{"__keyevent@5__:expired": self._expired_handler})
        for message in p.listen():
            self.logger.debug("Removed expired device {} from network {}".format(util.get_device_ip(message['data']), util.get_device_net(message['data'])))
            self.redis._del_device_from_network(util.get_device_ip(message['data']), util.get_device_net(message['data']))

    @staticmethod
    def stop():
        thread.exit()
