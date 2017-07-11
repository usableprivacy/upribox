# coding=utf-8
import thread
import logging
import threading

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import sniff, DHCP, hexstr
import sqlite3
from util import insert_or_update_fingerprint, DaemonError


class _SniffThread(threading.Thread):
    """This is an abstract class, which should be inherited to define the
    behaviour fo the sniffing thread."""

    _SNIFF_DIRECTION = "inbound"
    """str: speficies which traffic should be sniffed."""

    _SNIFF_FILTER = lambda self: "({}) and {}".format(" or ".join(zip(* self._SNIFF_PARTS)[0]), self._SNIFF_DIRECTION)
    """str: tcpdump filter used for scapy's sniff function."""
    # _SNIFF_FILTER = "(arp or igmp or (icmp6 and ip6[40] == 129) or (multicast and ip6[48] == 131) or (icmp6 and ip6[40] == 134)) and inbound"

    _LFILTER = lambda self, x: any([x.haslayer(layer) for layer in zip(* self._SNIFF_PARTS)[1]])
    # _LFILTER = staticmethod(lambda x: any([x.haslayer(layer) for layer in (ARP, IGMP, ICMPv6EchoReply, ICMPv6MLReport, ICMPv6ND_RA)]))
    """function: lambda filter used for scapy's sniff function."""

    def __init__(self, interface):
        """Initialises several things needed to define the thread's behaviour.

        Args:
            interface (str): The network interface which should be used. (e.g. eth0)
            ipv4 (namedtuple): Contains several information about the ipv4 configuration.
            ipv6 (namedtuple): Contains several information about the ipv6 configuration.
        """
        threading.Thread.__init__(self)
        self.interface = interface

    def run(self):
        """Starts sniffing for incoming ARP packets with scapy.
        Actions after receiving a packet ar defines via _packet_handler.
        """
        # the filter argument in scapy's sniff function seems to be applied too late
        # therefore some unwanted packets are processed (e.g. tcp packets of ssh session)
        # but it still decreases the number of packets that need to be processed by the lfilter function
        sniff(prn=self._packet_handler, filter=self._SNIFF_FILTER(), lfilter=self._LFILTER, store=0, iface=self.interface)

    def _packet_handler(self, pkt):
        """This method should be overriden to define the thread's behaviour."""
        pass

    @staticmethod
    def stop():
        """May be used to kill the thread, if it is not a daemon thread."""
        thread.exit()


class RegistrarSniffThread(_SniffThread):
    """Implements the abstract class _SniffThread and also implements
    the listener of the selective spoofing mode of Apate.
    """
    _SNIFF_PARTS = [("udp and (port 76 or port 68)", DHCP)]
    """list: List of tuples containing a BFP filter and the according scapy class."""

    def __init__(self, interface, logger, dbfile):
        """Initialises several things needed to define the thread's behaviour.

        Args:
            interface (str): The network interface which should be used. (e.g. eth0)
        """
        super(RegistrarSniffThread, self).__init__(interface)
        self.logger = logger
        self.dbfile = dbfile

    def _packet_handler(self, pkt):
        if pkt.haslayer(DHCP):
            # self.logger.error(pkt[DHCP].command())
            params = {}
            # dhcp request
            # options = dict(pkt[DHCP].options)
            # if options.get('message-type', 0) == 3 and options.get('requested_addr', None):
            for entry in pkt[DHCP].options:
                if entry[0] == "message-type":
                    params['message-type'] = entry[1]
                elif entry[0] == "vendor_class_id":
                    # self.logger.info("%s %s", entry[0], entry[1])
                    params['dhcp_vendor'] = entry[1]
                elif entry[0] == 'requested_addr':
                    params['ip'] = entry[1]
                elif entry[0] == 'hostname':
                    params['hostname'] = entry[1]
                elif entry[0] == "client_id":
                    # client_id value is hardware type (0x01) and mac address
                    params['mac'] = ":".join(hexstr(entry[1], onlyhex=True).split(" ")[-6:])
                elif entry[0] == 'param_req_list':
                    # DHCP fingerprint in fingerbank format
                    params['dhcp_fingerprint'] = ",".join([str(int(num, 16)) for num in hexstr(entry[1], onlyhex=True).split(" ")])

            if params.get('message-type', 0) == 3 and params.get('ip', None):
                try:
                    insert_or_update_fingerprint(self.conn, **params)
                except TypeError as te:
                    self.logger.error(insert_or_update_fingerprint.__name__ + " needs keyword-only argument ip")
                except sqlite3.Error as sqle:
                    self.logger.exception(sqle)

    def run(self):
        # db connection needs to be created in same thead as it is executed
        # therefore create it here
        try:
            self.conn = sqlite3.connect(self.dbfile)
        except sqlite3.Error as sqle:
            self.logger.error("Failed to connect to sqlite database at path %s" % (self.dbfile,))
            self.logger.exception(sqle)
            raise DaemonError()
        super(RegistrarSniffThread, self).run()

    # def stop(self):
    #     self.conn.close()
    #     super(RegistrarSniffThread, self).stop()
