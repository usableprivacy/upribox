# coding=utf-8
import logging
import socket
import sqlite3
import thread
import threading
import urllib2 as url
import xml
import errno

import xmltodict
from httplib import BadStatusLine
from netaddr import IPAddress
# suppresses following message
# WARNING: No route found for IPv6 destination :: (no default route?)
from scapy.all import BOOTP, DHCP, IP, UDP, Ether, hexstr, sniff
from util import (DaemonError, check_preconditions,
                  insert_or_update_fingerprint, insert_useragent)

# try to import C parser then fallback in pure python parser.
try:
    from http_parser.parser import HttpParser
except ImportError:
    from http_parser.pyparser import HttpParser

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)


class _SniffThread(threading.Thread):
    """This is an abstract class, which should be inherited to define the
    behaviour fo the sniffing thread."""

    _SNIFF_DIRECTION = "inbound"
    """str: speficies which traffic should be sniffed."""

    _SNIFF_FILTER = lambda self: "({}) and {}".format(" or ".join(["(" + part + ")" for part in zip(*self._SNIFF_PARTS)[0]]), self._SNIFF_DIRECTION)
    """str: tcpdump filter used for scapy's sniff function."""
    # _SNIFF_FILTER = "(arp or igmp or (icmp6 and ip6[40] == 129) or (multicast and ip6[48] == 131) or (icmp6 and ip6[40] == 134)) and inbound"

    _LFILTER = lambda self, x: any([x.haslayer(layer) for layer in zip(*self._SNIFF_PARTS)[1]])
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
    _SNIFF_PARTS = [
        ("udp and (port 67 or port 68)", DHCP),
        ("udp and port 1900", UDP),
    ]
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
        try:
            if pkt.haslayer(DHCP):
                self._handle_dhcp(pkt)
            elif pkt.haslayer(UDP) and pkt[UDP].dport == 1900:
                self._handle_ssdp(pkt)
        except Exception as e:
            self.logger.error("Failed to handle packet")
            self.logger.exception(e)

    def run(self):
        # db connection needs to be created in same thead as it is executed
        # therefore create it here
        try:
            self.conn = sqlite3.connect(self.dbfile)
        except sqlite3.Error as sqle:
            self.logger.error("Failed to connect to sqlite database at path %s" % (self.dbfile, ))
            self.logger.exception(sqle)
            raise DaemonError()
        super(RegistrarSniffThread, self).run()

    def _handle_dhcp(self, pkt):
        # self.logger.error(pkt[DHCP].command())
        params = {}
        params['mac'] = ":".join(hexstr(pkt[BOOTP].chaddr, onlyhex=True).split(" ")[:6])

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
            elif entry[0] == 'param_req_list':
                # DHCP fingerprint in fingerbank format
                params['dhcp_fingerprint'] = ",".join([str(int(num, 16)) for num in hexstr(entry[1], onlyhex=True).split(" ")])

        if params.get('message-type', 0) == 3 and check_preconditions(params.get('ip', None), params.get('mac', None)):
            try:
                insert_or_update_fingerprint(self.conn, **params)
                self.logger.debug("registered dhcp: ip: {}, mac: {}".format(params.get('ip', None), params.get('mac', None)))
            except TypeError as te:
                self.logger.error(insert_or_update_fingerprint.__name__ + " needs keyword-only argument ip")
            except sqlite3.Error as sqle:
                self.logger.exception(sqle)
            except ValueError as ve:
                self.logger.exception(ve)

    def _handle_ssdp(self, pkt):
        parser = HttpParser()
        params = {}
        user_agents = []
        id = None

        if not all(pkt.haslayer(layer) for layer in [Ether, IP, UDP]):
            self.logger.debug("packet does not contain all required layers")
            self.logger.debug(pkt.command())
            return

        params['mac'] = pkt[Ether].src
        params['ip'] = pkt[IP].src

        if check_preconditions(params.get('ip', None), params.get('mac', None)):
            try:
                id = insert_or_update_fingerprint(self.conn, **params)
                self.logger.debug("registered ssdp: ip: {}, mac: {}".format(params.get('ip', None), params.get('mac', None)))
            except TypeError as te:
                self.logger.error(insert_or_update_fingerprint.__name__ + " needs keyword-only argument ip")
            except sqlite3.Error as sqle:
                self.logger.exception(sqle)

        if id is None:
            return

        if parser.execute(pkt[UDP].payload.load, len(pkt[UDP].payload.load)) != len(pkt[UDP].payload.load):
            self.logger.warning("error while parsing HTTP payload of ssdp packet")
            return

        headers = parser.get_headers()
        if "user-agent" in headers:
            # e.g. chrome appends user agent to ssdp:discover
            user_agents.append((headers['user-agent'], False))

        if "server" in headers:
            user_agents.append((headers['server'], False))

        if "location" in headers:
            req = url.Request(headers['location'])
            host = ""
            ip = None
            try:
                ip = socket.gethostbyname_ex(req.get_host().split(":")[0])
            except ValueError:
                self.logger.warning("malformed location value")
            except socket.error:
                self.logger.warning("Unable to get ip of host")
            else:
                # only allow locations inside private networks
                if IPAddress(ip[2][0]).is_private():
                    try:
                        xml_content = url.urlopen(req).read()
                        spec = xmltodict.parse(xml_content)
                        user_agents.append((spec['root']['device']['friendlyName'], True))
                    except url.URLError as urle:
                        self.logger.warning("Unable to get content of url " + headers['location'])
                        self.logger.warning(urle)
                    except xml.parsers.expat.ExpatError:
                        self.logger.error("Unable to parse upnp xml from url " + headers['location'])
                    except KeyError:
                        self.logger.error("xml does not contain required friendlyName from url " + headers['location'])
                    except BadStatusLine:
                        self.logger.warning("Server responded with bad status line for url " + headers['location'])
                    except socket.error as e:
                        if e.errno != errno.ECONNRESET:
                            raise
                        self.logger.warning("Connection reset by peer connecting to url " + headers['location'])
                    else:
                        try:
                            user_agents.append((spec['root']['device']['modelDescription'], True))
                        except KeyError:
                            # modelDescription is not mandatory, only recommended
                            pass

        for agent, model in user_agents:
            insert_useragent(self.conn, agent, id, model)
