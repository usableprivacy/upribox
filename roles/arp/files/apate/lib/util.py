# coding=utf-8
"""Provides several useful functions used by other modules."""
import logging
from netaddr import IPAddress

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import srp, ARP, Ether, ETHER_BROADCAST, IPv6, ICMPv6ND_NS


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
        interface (str): Interface used to send ARP request.

    Results:
        According MAC address as string (11:22:33:44:55:66)
        or None if no answer has been received.
    """
    ans, unans = srp(Ether(dst=ETHER_BROADCAST) / ARP(pdst=ip), timeout=2, iface=interface, inter=0.1, verbose=0)
    for snd, rcv in ans:
        return rcv.sprintf(r"%Ether.src%")


def get_mac6(ip, interface):
    """Returns the according MAC address for the provided IPv6 address.

    Args:
        ip (str): IPv6 address used to get MAC address.
        interface (str): Interface used to send neighbor solicitation.

    Results:
        According MAC address as string (11:22:33:44:55:66)
        or None if no answer has been received.
    """
    ans, unans = srp(Ether(dst=ETHER_BROADCAST) / IPv6(dst=ip) / ICMPv6ND_NS(tgt=ip), timeout=2, iface=interface, inter=0.1, verbose=0)
    for snd, rcv in ans:
        return rcv.sprintf(r"%Ether.src%")


def get_device_enabled(redis_device):
    """Returns the enabled part of a device entry."""
    return redis_device.rsplit("|", 1)[-1]


def get_device_mac(redis_device):
    """Returns the mac address part of a device entry."""
    return redis_device.rsplit("|", 2)[-2]


def get_device_net(redis_device):
    """Returns the network address part of a device entry."""
    return redis_device.split("|", 3)[2]


def is_spoof_dns(ipv6):
    """Checks if it is necessary to additionally spoof the address of the DNS server.
    The DNS server needs to be spoofed if it is on the own network and if it is not
    the default gateway (this is already used for spoofing).

    Args:
        ipv6 (namedtuple): Contains various IPv6 information.
        ipv6.dns_servers (list): List containing the IP addresses of DNS servers as String.
        ipv6.network (netaddr.IPNetwork): IPNetwork object representing the IPv6 network.
        ipv6.gateway (str): IPv6 address of the default gateway.

    Results:
        True if configured DNS server uses a global address and is on own network
        or DNS server uses link-local address and is not also the gateway.
    """
    return ipv6.dns_servers[0] in ipv6.network or (IPAddress(ipv6.dns_servers[0]).is_link_local()
                                                   and ipv6.dns_servers[0] != ipv6.gateway)


# class IPInfo(object):
#
#     def __init__(self, ip, netmask, network, gateway, mac, gate_mac, dns_servers, redis):
#         self.ip = ip
#         self.netmask = netmask
#         self.mac = mac
#         self.network = network
#         self.gateway = gateway
#         self.gate_mac = gate_mac
#         self.dns_servers = dns_servers
#         self.redis = redis
