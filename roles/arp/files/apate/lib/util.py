# coding=utf-8
"""Provides several useful functions used by other modules."""
import logging

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import srp, ARP, Ether, ETHER_BROADCAST


def hex2str_mac(hex_val):
    r"""Converts a hex mac address into a human-readable string representation.

    Example:
        "\x11\x22\x33\x44\x55\x66"  -->  "11:22:33:44:55:66"

    Args:
        hex_val (str): String containg a mac address as hex values.

    Results:
        str: Human-readably MAC address.

    """
    return ':'.join(["{:02x}".format(ord(x)) for x in hex_val])


def get_mac(ip, interface):
    """Returns the according MAC address for the provided IP address.

    Args:
        ip (str): IP address used to get MAC address.
        interface (str): Interface used to send ARP reuest.

    Results:
        According MAC address as string (11:22:33:44:55:66)
        or None if no answer has been received.
    """
    ans, unans = srp(Ether(dst=ETHER_BROADCAST) / ARP(pdst=ip), timeout=2, iface=interface, inter=0.1, verbose=0)
    for snd, rcv in ans:
        return rcv.sprintf(r"%Ether.src%")


def get_device_enabled(redis_device):
    """Returns the enabled part of a device entry."""
    return redis_device.rsplit(":", 1)[-1]


def get_device_ip(redis_device):
    """Returns the ip address part of a device entry."""
    return redis_device.rsplit(":", 2)[-2]


def get_device_net(redis_device):
    """Returns the network address part of a device entry."""
    return redis_device.split(":", 3)[2]
