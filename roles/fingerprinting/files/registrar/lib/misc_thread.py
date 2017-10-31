# coding=utf-8
import logging
import threading
import time

from scapy.all import IP, UDP, Ether, conf, send

# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)


class SSDPDiscoveryThread(threading.Thread):
    _SLEEP = 10
    """int: Time to wait before sending packets anew."""

    _PORT = 1900
    _DST = "239.255.255.250"

    _PAYLOAD = "M-SEARCH * HTTP/1.1\r\n" \
        "HOST:239.255.255.250:1900\r\n" \
        "ST:upnp:rootdevice\r\n" \
        "MAN: \"ssdp:discover\"\r\n" \
        "MX:2\r\n\r\n"

    def __init__(self, interface):
        """Initialises the thread.
        """
        threading.Thread.__init__(self)
        self.interface = interface

    def run(self):
        while True:
            send(IP(dst=self._DST) / UDP(sport=self._PORT, dport=self._PORT) / self._PAYLOAD, iface=self.interface)
            time.sleep(self._SLEEP)
