# coding=utf-8
import logging
import sqlite3
import threading
import time

from scapy.all import ARP, IP, UDP, Ether, arping, conf, send
from util import DaemonError, check_preconditions, insert_or_update_fingerprint

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


class StaticIPNoModeDiscoveryThread(threading.Thread):
    _SLEEP = 3600
    """int: Time to wait before sending packets anew."""
    _QUERY = "select ip from devices_deviceentry where mode='NO'"

    def __init__(self, interface, dbfile, logger):
        """Initialises the thread.
        """
        threading.Thread.__init__(self)
        self.interface = interface
        self.dbfile = dbfile
        self.logger = logger

    def run(self):
        try:
            self.conn = sqlite3.connect(self.dbfile)
            with self.conn:
                c = self.conn.cursor()
                while True:
                    try:
                        c.execute(self._QUERY)
                        devices = list(sum(c.fetchall(), ()))

                        if devices:
                            ans, unans = arping(devices, iface=None, verbose=0)
                            for device in ans:
                                ip_addr = device[1][ARP].psrc
                                mac_addr = str(device[1][ARP].hwsrc).lower()
                                if check_preconditions(ip_addr, mac_addr):
                                    insert_or_update_fingerprint(self.conn, ip=ip_addr, mac=mac_addr)

                        self.logger.info("checked no mode devices: " + str(devices))

                        time.sleep(self._SLEEP)
                    except sqlite3.Error as sqle:
                        self.logger.error("a database error occurred")
                        self.logger.exception(sqle)
        except sqlite3.Error as sqle:
            self.logger.error("Failed to connect to sqlite database at path %s" % (self.dbfile, ))
            self.logger.exception(sqle)
            raise DaemonError()
