import re
import socket
import sys
sys.path.insert(0, "/usr/share/nginx/www-upri-interface/lib/")
sys.path.insert(0, "/opt/apate/lib/")
import netifaces as ni
from netaddr import IPNetwork


def check_passwd(arg):
    import passwd
    pw = passwd.Password(arg)
    if not pw.is_valid():
        if not pw.has_digit():
            print 'the password must contain at least 1 digit'
        if not pw.has_lowercase_char():
            print 'the password must contain at least 1 lowercase character'
        if not pw.has_uppercase_char():
            print 'the password must contain at least 1 uppercase character'
        if not pw.has_symbol():
            print 'the password must contain at least 1 special character'
        if not pw.has_allowed_length():
            print 'the password must be between 8 to 63 characters long'
        if not pw.has_only_allowed_chars():
            print 'the password must only contain following special characters: %s' % pw.get_allowed_chars()

        return False
    else:
        return True


def check_ssid(arg):
    import ssid
    ssid_value = ssid.SSID(arg)
    if not ssid_value.is_valid():
        if not ssid_value.has_allowed_length():
            print 'the password must be between 1 to 32 characters long'
        if not ssid_value.has_only_allowed_chars():
            print 'the ssid must only contain following special characters: %s' % ssid_value.get_allowed_chars()

        return False
    else:
        return True


def check_domain(arg):
    import domain
    domain_value = domain.Domain(arg)
    if not domain_value.is_valid():
        if not domain_value.has_allowed_length():
            print 'the password can only contain up to 255 characters'
        if not domain_value.has_only_allowed_chars():
            print 'the domain must only contain following special characters: %s' % domain_value.get_allowed_chars()

        return False
    else:
        return True


def check_mac(mac):
    return re.match("[0-9a-f]{2}([:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower())


def check_ip(ip):
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return socket.AF_INET
    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, ip)
            return socket.AF_INET6
        except socket.error:
            return None
    except TypeError:
        return None


def get_network(interface, addr_family):
    if_info = None
    try:
        if_info = ni.ifaddresses(interface)
    except ValueError as e:
        print "An error concerning the interface {} has occurred: {}".format(interface, str(e))
        return None
    # get subnetmask of specified interface
    try:
        addr = if_info[addr_family][0]['addr']
        netmask = if_info[addr_family][0]['netmask'].split("/")[0]
        return str(IPNetwork("{}/{}".format(addr, netmask)).network)
    except IndexError:
        return None
