import logging

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import conf, srp, ARP, Ether, ETHER_BROADCAST


def hex2str_mac(hex_val):
    return ':'.join(["{:02x}".format(ord(x)) for x in hex_val])


def get_mac(ip, interface):
    ans, unans = srp(Ether(dst=ETHER_BROADCAST) / ARP(pdst=ip), timeout=2, iface=interface, inter=0.1, verbose=0)
    for snd, rcv in ans:
        return rcv.sprintf(r"%Ether.src%")


def get_device_enabled(redis_device):
    return redis_device.rsplit(":", 1)[-1]


def get_device_ip(redis_device):
    return redis_device.rsplit(":", 2)[-2]


def get_device_net(redis_device):
    return redis_device.split(":", 3)[2]