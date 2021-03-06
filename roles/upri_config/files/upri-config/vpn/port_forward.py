import miniupnpc
import sys
import requests
import subprocess
import re
from os.path import exists

from lib.utils import check_fact


# Port for OpenVPN
PORT = check_fact('vpn', 'connection', 'port', debug=False)
PROTOCOL = check_fact('vpn', 'connection', 'protocol', debug=False)
CERT_DNS_PATH = check_fact('vpn', 'general', 'cert_dns_path', debug=False)
SSL_PINNING_PATH = check_fact('vpn', 'general', 'ssl_pinning_path', debug=False)

# Regex for parsing NATPMP output
PUB_IP_REGEX = r'\bPublic IP address : (?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
IPV4_REGEX = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'

debug = False

# Comparison of public IP with saved one, if new is found, update dns
# return values:
# 1: error in file handling(read/write)


def update_public_ip(pub_ip):
    # Load saved public IP
    try:
        if debug:
            print 'Load saved public IP from file'
        # Read from file and create file if doesn't exist
        with open('/tmp/ip.txt', 'a+') as f:
            pub_ip_svd = f.readline()

            if debug:
                print ' Saved public IP:', pub_ip_svd

        if pub_ip_svd != pub_ip:
            with open('/tmp/ip.txt', 'w') as f:
                if debug:
                    print 'Save public IP to file'
                f.write(pub_ip)
                dns_update()

    except IOError as e:
        if debug:
            print ' Exception :', e
            print 'Public IP cannot be loaded'
        return 1

    return 0

# DNS update
# return values:
# 1: HTTPS request failed


def dns_update():
    if debug:
        print 'Send DNS update'
    try:
        if exists(CERT_DNS_PATH):
            r = requests.get('https://api.upribox.org/dnsupdate/', cert=CERT_DNS_PATH, timeout=3, verify=SSL_PINNING_PATH)
            if debug:
                if r.text == 'OK':
                    print ' DNS Update Successful'
                else:
                    print ' Error - DNS update not successful'
                    return 1
        else:
            return 1
    except Exception, e:
        if debug:
            print ' Exception :', e
        return 1

    return 0


def get_upnp_devices():
    # Check if UPNP is available and set port forwarding
    upnpc = miniupnpc.UPnP()

    # Discover UPNP devices
    upnpc.discoverdelay = 200

    if debug:
        print 'Check UPNP Support'

    try:
        ndevices = upnpc.discover()
        if debug:
            print ' %d UPNP device(s) detected' % (ndevices)

        if ndevices:
            upnpc.selectigd()
            return upnpc
    except Exception:
        if debug:
            print ' No appropriate UPNP device available'
        return None


def get_upnp_public_ip(upnp_devices):
    public_ip = None
    try:
        public_ip = upnp_devices.externalipaddress()
    except:
        if debug:
            print "Could not get public IP via upnp."
    # If UPNP device with public IP is found activate port forwarding
    if public_ip and debug:
        print ' internal ip: ', upnp_devices.lanaddr
        print ' external ip: ', public_ip
        print ' status: %s, connection type: %s' % (upnp_devices.statusinfo(), upnp_devices.connectiontype())
    return public_ip


def set_upnp_port_mapping(upnp_devices):
    # Check current port mapping status
    port_available = False
    port_response = None
    port_already_mapped = False

    try:
        port_response = upnp_devices.getspecificportmapping(PORT, str(PROTOCOL))
        if port_response is None:
            port_available = True
        else:
            if 'upri.box OpenVPN port' in port_response[2]:
                if debug:
                    print ' upri.box OpenVPN port already mapped!'
                port_already_mapped = True
                return True
            elif debug:
                print ' Port already in use by other application!', port_response
    except:
        print "Could probe if upnp port is available"

    if debug:
        print ' Enable port forwarding with UPNP'

    if port_available and not port_already_mapped:
        try:
            s = upnp_devices.addportmapping(PORT, str(PROTOCOL), upnp_devices.lanaddr, PORT, 'upri.box OpenVPN port', '')
            if s:
                if debug:
                    print 'Successful port mapping,  %s:%s - %s:%s' % (upnp_devices.lanaddr, PORT, upnp_devices.externalipaddress(), PORT)
                    return True
        except:
            return False
    if debug:
        print ' Execption: Adding port mapping not possible'

    return False


def check_natpmp_support():
    natpmp_chk = 'natpmpc'

    p = subprocess.Popen(natpmp_chk, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return_code = p.returncode

    if return_code == 0:
        if debug:
            print 'NATPMP supported.'
        return True
    elif debug:
        print "NATPMP not supported: " + stderr

    return False


def set_natpmp_mapping():
    natpmp_en = ['natpmpc', '-a', str(PORT), str(PORT), str(PROTOCOL), '86400']
    p = subprocess.Popen(natpmp_en, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return_code = p.returncode

    if debug:
        print stdout, stderr

    if return_code != 0:
        return False

    for line in stdout:
        if re.match(PUB_IP_REGEX, line):
            pub_ip_natpmp = line
            public_ip = re.findall(IPV4_REGEX, pub_ip_natpmp)
            if debug:
                print ' public IP: ', public_ip
            update_public_ip(public_ip)

    return True


def action_forward(arg):

    if arg == True:
        global debug
        debug = True

    public_ip = None
    upnpn_mapping_successful = False
    natpmp_mapping_successful = False

    upnp_devices = get_upnp_devices()

    if upnp_devices:
        public_ip = get_upnp_public_ip(upnp_devices)
        upnpn_mapping_successful = set_upnp_port_mapping(upnp_devices)
    elif debug:
        print "UPNP not supported."

    if public_ip is not None and upnpn_mapping_successful:
        update_public_ip(public_ip)
        dns_update()
        return 0

    if check_natpmp_support():
        natpmp_mapping_successful = set_natpmp_mapping()
    elif debug:
        print "NATPMP not supported."

    if natpmp_mapping_successful:
        dns_update()
        return 0

    dns_update()
