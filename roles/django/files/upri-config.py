#!/usr/bin/env python
import json
import sys
import subprocess
from jsonmerge import merge
from os import path, chmod
import sys
sys.path.insert(0, "/usr/share/nginx/www-upri-interface/lib/")
sys.path.insert(0, "/opt/apate/lib/")
import passwd
import ssid
import domain
import re
from datetime import datetime
import time
from urlparse import urlparse
import os
import sqlite3
import logging
logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
from apate_redis import ApateRedis
import socket
import netifaces as ni
from netaddr import IPNetwork, IPAddress, ZEROFILL
import redis as redisDB
# import traceback

# directory where facts are located
FACTS_DIR = "/etc/ansible/facts.d"
# path to the ansible-playbook executeable
ANSIBLE_COMMAND = "/usr/local/bin/ansible-playbook"
# path to the used inventory
ANSIBLE_INVENTORY = "/var/lib/ansible/local/environments/production/inventory_pull"
# path to the used playbook
ANSIBLE_PLAY = "/var/lib/ansible/local/local.yml"
# path to the openvpn client config template
CLIENT_TEMPLATE = "/etc/openvpn/client_template"
CONFIG_FILE = "/etc/apate/config.json"

# default value of mode column of devices_deviceentry table
_DEVICE_DEFAULT_MODE = "SL"

def action_disable_device(arg):
    if not check_ip(arg):
        return 27

    return toggle_device(arg, False)


def action_enable_device(arg):
    if not check_ip(arg):
        return 27

    return toggle_device(arg, True)


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


def toggle_device(ip, enabled):
    try:
        with open(CONFIG_FILE) as config:
            data = json.load(config)
    except ValueError as ve:
        print "Could not parse the configuration file"
        print str(ve)
        return 28
    except IOError as ioe:
        print "An error occurred while trying to open the configuration file"
        print str(ioe)
        return 29

    if 'interface' not in data:
        print "The configuration file does not include all necessary options"
        return 30

    network = get_network(data['interface'], check_ip(ip))
    if not network:
        return 31

    try:
        redis = ApateRedis(network, logging.getLogger('config'))
        if enabled:
            redis.enable_device(ip, network)
        else:
            redis.disable_device(ip, network)
    except:
        return 32

    return 0

redis = redisDB.StrictRedis(host="localhost", port=6379, db=7)

# syntax for keys in redis db for statistics
__PREFIX = "stats"
"""str: Prefix which is used for every key in the redis db."""
__DELIMITER = ":"
"""str: Delimiter used for separating parts of keys in the redis db."""
__DNSMASQ = "dnsmasq"
__PRIVOXY = "privoxy"
__BLOCKED = "blocked"
__ADFREE = "adfree"
__MONTH = "month"
__DAY = "day"
__DOMAIN = "domain"

#
# revokes previously generated openvpn client certificates
# return values:
# 26 failed to revoke certificate


def action_delete_profile(slug):
    try:
        filename = os.path.basename(slug)

        rc = subprocess.call(['/usr/bin/openssl', 'ca', '-revoke', '/etc/openvpn/ca/%sCert.pem' % filename])
        rc = subprocess.call(['/usr/bin/openssl', 'ca', '-gencrl', '-crlhours', '1', '-out', '/etc/openssl/demoCA/crl.pem'])

        #os.remove('/etc/openvpn/ca/%sKey.pem' % filename)
        #os.remove('/etc/openvpn/ca/%sCert.pem' % filename)

    except Exception as e:
        print "failed to delete client files"
        print str(e)
        return 26

    return 0

#
# generate openvpn client certificates and saves the
# generated openvpn client config into the database
# return values:
# 16: database error
# 21: entry does not exists in database
# 24: provided domain is not valid
# 23: unable to create client certificate files
# 22: openvpn client template is missing


def action_generate_profile(profile_id):
    with open('/etc/ansible/default_settings.json', 'r') as f:
        config = json.load(f)

    dbfile = config['django']['db']

    try:
        conn = sqlite3.connect(dbfile)
        c = conn.cursor()
        c.execute("SELECT slug,dyndomain FROM vpn_vpnprofile WHERE id=?", (profile_id,))
        data = c.fetchone()
        if not data:
            # invalid profile id
            print 'profile id does not exist in database'
            return 21

        slug = data[0]
        dyndomain = data[1]

        if not check_domain(dyndomain):
            return 24

        dyndomain = domain.Domain(data[1]).get_match()

        filename = os.path.basename(slug)

        rc = subprocess.call(['/usr/bin/openssl', 'req', '-newkey', 'rsa:2048', '-nodes', '-subj', "/C=AT/ST=Austria/L=Vienna/O=Usable Privacy Box/OU=VPN/CN=%s" %
                              filename, '-keyout', '/etc/openvpn/ca/%sKey.pem' % filename, '-out', '/etc/openvpn/ca/%sReq.pem' % filename])

        chmod('/etc/openvpn/ca/%sKey.pem' % filename, 0640)

        if rc != 0:
            print "error while creating client certificate reques"
            return 23

        subprocess.call(['/usr/bin/openssl', 'ca', '-in', '/etc/openvpn/ca/%sReq.pem' % filename, '-days', '730', '-batch', '-out', '/etc/openvpn/ca/%sCert.pem' %
                         filename, '-notext', '-cert', '/etc/openvpn/ca/caCert.pem', '-keyfile', '/etc/openvpn/ca/caKey.pem'])

        if rc != 0:
            print "error while creating client certificate"
            return 23

        os.remove('/etc/openvpn/ca/%sReq.pem' % filename)

        if os.path.isfile(CLIENT_TEMPLATE):
            with open(CLIENT_TEMPLATE, 'r') as template, open('/etc/openvpn/ca/%sKey.pem' % filename, 'r') as client_key, open('/etc/openvpn/ca/%sCert.pem' % filename, 'r') as client_cert:
                temp = template.read()
                temp = temp.replace("#CLIENT_KEY", client_key.read())
                temp = temp.replace("#CLIENT_CERT", client_cert.read())
                temp = temp.replace("<IP-ADRESS>", dyndomain)

                c.execute("UPDATE vpn_vpnprofile SET config=? where id=?", (temp, profile_id))
                conn.commit()
        else:
            print "client template is missing"
            return 22

        conn.close()
    except Exception as e:
        print "failed to write to database"
        print str(e)
        return 16
    return 0

#
# parse the privoxy and dnsmasq logfiles and insert data into django db
# return values:
# 16: error
# 1: new entries have been added
# 0: no changes


def action_parse_logs(arg):
    dnsmasq_val = parse_dnsmasq_logs(arg)
    privoxy_val = parse_privoxy_logs(arg)
    if 16 in (privoxy_val, dnsmasq_val):
        return 16
    elif 1 in (privoxy_val, dnsmasq_val):
        return 1
    else:
        return 0

#
# parse the privoxy logfiles and insert data into django db
# return values:
# 16: error
# 1: new entries have been added
# 0: no changes


def parse_privoxy_logs(arg):
    rlog = re.compile('(\d{4}-\d{2}-\d{2} (\d{2}:?){3}).\d{3} [a-z0-9]{8} Crunch: Blocked: (.*)')

    changed = False
    with open('/etc/ansible/default_settings.json', 'r') as f:
        config = json.load(f)

    logfile = os.path.join(config['log']['general']['path'], config['log']['privoxy']['subdir'],
                           config['log']['privoxy']['logfiles']['logname'])

    if os.path.isfile(logfile):
        print "parsing privoxy logfile %s" % logfile
        with open(logfile, 'r') as privoxy:
            for line in privoxy:
                try:
                    res = re.match(rlog, line)
                    if res:
                        sdate = res.group(1)
                        ssite = res.group(3)
                        pdate = datetime.strptime(sdate, '%Y-%m-%d %H:%M:%S')
                        month = pdate.month
                        psite = urlparse(ssite).netloc
                        # increments value of domain by 1 or sets to 1 if domain does not exist yet
                        redis.incr(__DELIMITER.join((__PREFIX, __PRIVOXY, __BLOCKED, __DOMAIN, psite)))

                        # increments value of month by 1 or sets to 1 if the month does not exist yet
                        redis.incr(__DELIMITER.join((__PREFIX, __PRIVOXY, __BLOCKED, __MONTH, str(month))))

                        changed = True
                        print "found new block: [%s] %s" % (sdate, psite)
                except Exception as e:
                    print "failed to parse line \"%s\": %s" % (line, e.message)

        if changed:
            try:
                # truncate logfile
                with open(logfile, "a") as lf:
                    lf.truncate(0)
                #subprocess.call(["/usr/sbin/service", "privoxy", "restart"])
            except Exception as e:
                print "failed to write to redis database"
                return 16
            return 1
    else:
        print "failed to parse privoxy logfile %s: file not found" % logfile
        return 16

    return 0
#
# parse the dnsmasq logfile and insert data into django db
# DnsmasqQueryLogEntry contains all queries (blocked and unblocked)
# DnsmasqFilteredLogEntry contains only blocked queries
# return values:
# 16: error
# 1: new entries have been added
# 0: no changes


def parse_dnsmasq_logs(arg):
    queryPattern = re.compile('([a-zA-Z]{3} ? \d{1,2} (\d{2}:?){3}) dnsmasq\[[0-9]*\]: query\[[A-Z]*\] (.*) from ([0-9]+.?){4}')
    blockedPattern = re.compile('([a-zA-Z]{3} ? \d{1,2} (\d{2}:?){3}) dnsmasq\[[0-9]*\]: config (.*) is 192.168.55.254')

    changed = False
    with open('/etc/ansible/default_settings.json', 'r') as f:
        config = json.load(f)

    logfile = os.path.join(config['log']['general']['path'], config['log']['dnsmasq']['subdir'],
                           config['log']['dnsmasq']['logfiles']['logname'])

    if os.path.isfile(logfile):
        print "parsing dnsmasq logfile %s" % logfile
        cur_year = time.localtime().tm_year
        with open(logfile, 'r') as dnsmasq:
            for line in dnsmasq:
                try:
                    res = re.match(queryPattern, line)
                    if res:
                        sdate = res.group(1)
                        ssite = res.group(3)
                        psite = str(ssite)
                        pdate = datetime.strptime(sdate, '%b %d %H:%M:%S')
                        pdate = pdate.replace(year=cur_year)
                        date = pdate.strftime('%Y-%m-%d')
                        month = pdate.month

                        # increments value of today's date by 1 or sets to 1 if the date does not exist yet
                        redis.incr(__DELIMITER.join((__PREFIX, __DNSMASQ, __ADFREE, __DAY, date)))

                        # increments value of month by 1 or sets to 1 if the month does not exist yet
                        redis.incr(__DELIMITER.join((__PREFIX, __DNSMASQ, __ADFREE, __MONTH, str(month))))

                        changed = True

                        print "found new query: [%s] %s" % (psite, pdate)
                except Exception as e:
                    print "failed to parse query \"%s\": %s" % (line, e.message)

                try:
                    res = re.match(blockedPattern, line)
                    if res:
                        sdate = res.group(1)
                        ssite = res.group(3)
                        psite = str(ssite)
                        pdate = datetime.strptime(sdate, '%b %d %H:%M:%S')
                        pdate = pdate.replace(year=cur_year)
                        date = pdate.strftime('%Y-%m-%d')
                        month = pdate.month

                        # increments value of today's date by 1 or sets to 1 if the date does not exist yet
                        redis.incr(__DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, __DAY, date)))

                        # increments value of domain by 1 or sets to 1 if domain does not exist yet
                        redis.incr(__DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, __DOMAIN, psite)))

                        # increments value of month by 1 or sets to 1 if the month does not exist yet
                        redis.incr(__DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, __MONTH, str(month))))

                        changed = True

                        print "found new blocked query: [%s] %s" % (psite, pdate)
                except Exception as e:
                    print "failed to parse blocked query \"%s\": %s" % (line, e.message)

        if changed:
            try:
                # truncate logfile
                with open(logfile, "a") as lf:
                    lf.truncate(0)
                #subprocess.call(["/usr/sbin/service", "dnsmasq", "restart"])
            except Exception as e:
                print "failed to write to redis database"
                return 16
            return 1
    else:
        print "failed to parse dnsmasq logfile %s: file not found" % logfile
        return 16

    return 0
#
# parse the squid logfile and insert new user-agents into django db
# return values:
# 16: error
# 1: new entries have been added
# 0: no changes


def action_parse_user_agents(arg):
    errors = False

    with open('/etc/ansible/default_settings.json', 'r') as f:
        config = json.load(f)

    dbfile = config['django']['db']
    logfile = os.path.join(config['log']['general']['path'], config['log']['squid']['subdir'],
                           config['log']['squid']['logfiles']['logname'])

    if os.path.isfile(logfile):
        print "parsing squid logfile %s" % logfile
        with open(logfile, 'r') as squid:
            try:
                conn = sqlite3.connect(dbfile)
                c = conn.cursor()
                for line in squid:
                    with conn:
                        parts = line.strip().split(";|;")
                        agent_id = None
                        try:
                            c.execute("INSERT INTO devices_useragent (agent) VALUES (?)", (parts[2],))
                            agent_id = c.lastrowid
                        except sqlite3.IntegrityError as sqlie:
                            if "UNIQUE constraint failed: devices_useragent.agent" in sqlie.message:
                                c.execute("SELECT id FROM devices_useragent WHERE agent=?", (parts[2],))
                                try:
                                    agent_id = c.fetchone()[0]
                                except (TypeError, IndexError):
                                    raise ValueError("Unable to retrieve id of useragent string")
                            else:
                                raise sqlie

                        device_id = None
                        try:
                            c.execute("INSERT INTO devices_deviceentry (ip, mac, mode) VALUES (?, ?, ?)", (parts[1], parts[0], _DEVICE_DEFAULT_MODE))
                            device_id = c.lastrowid
                        except sqlite3.IntegrityError as sqlie:
                            if "UNIQUE constraint failed: devices_deviceentry.mac" in sqlie.message:
                                c.execute("SELECT id, ip from devices_deviceentry where mac=?", (parts[0],))
                                res = c.fetchone()
                                if not res:
                                    raise ValueError("Unable to retrieve id of device")

                                device_id = res[0]
                                if res[1] != parts[1]:
                                    c.execute("UPDATE devices_deviceentry SET ip=? where mac=?", (parts[1], parts[0]))
                            else:
                                raise sqlie

                        try:
                            if agent_id is not None and device_id is not None:
                                c.execute("INSERT INTO devices_deviceentry_user_agent (deviceentry_id, useragent_id) values (?, ?)", (str(device_id), str(agent_id)))
                        except sqlite3.IntegrityError:
                            # entry already exists
                            pass

                conn.close()
            except sqlite3.Error as sqle:
                print sqle.message
                errors = True
                # traceback.print_exc()
            except Exception as e:
                print "failed to parse user-agent \"%s\": %s" % (line.strip(), e.message)
                errors = True
        if not errors:
            try:
                # truncate logfile
                with open(logfile, "a") as lf:
                    lf.truncate(0)
            except Exception as e:
                print "failed to restart service"
                return 16

            rc = subprocess.call(["/var/webapp-virtualenv/bin/python", "/usr/share/nginx/www-upri-interface/manage.py", "fingerprint", "--settings", config['django']['settings']])
            if rc != 0:
                print "user agent parsing failed"
                return 16

            return 1
    else:
        print "failed to parse squid logfile %s: file not found" % logfile
        return 16

    return 0


def action_set_ip(arg):
    print 'setting ip to "%s"' % arg
    ip = None
    try:
        ip = IPAddress(arg, flags=ZEROFILL)
    except:
        return 12

    obj = {"static": {"ip": str(ip)}}
    write_role('interfaces', obj)


def action_set_dns_server(arg):
    print 'setting ip to "%s"' % arg
    ip = None
    try:
        ip = IPAddress(arg, flags=ZEROFILL)
    except:
        return 12

    obj = {"static": {"dns": str(ip)}}
    write_role('interfaces', obj)


def action_set_netmask(arg):
    print 'setting ip to "%s"' % arg
    ip = None
    try:
        ip = IPAddress(arg, flags=ZEROFILL)
        if not ip.is_netmask():
            return 13
    except:
        return 12

    obj = {"static": {"netmask": str(ip)}}
    write_role('interfaces', obj)


def action_set_gateway(arg):
    print 'setting ip to "%s"' % arg
    ip = None
    try:
        ip = IPAddress(arg, flags=ZEROFILL)
    except:
        return 12

    obj = {"static": {"gateway": str(ip)}}
    write_role('interfaces', obj)


def action_restart_network(arg):
    print 'restarting network...'
    return call_ansible('network_config')


def action_set_dhcpd(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'DHCP server enabled: %s' % arg
    en = {"general": {"enabled": arg}}
    write_role('dhcpd', en)


def action_restart_dhcpd(arg):
    print 'restarting dhcp server...'
    return call_ansible('dhcp_server')

#
# set a new ssid for the upribox "silent" wlan
# return values:
# 12: ssid does not meet policy
#


def action_set_ssid(arg):
    print 'setting ssid to "%s"' % arg
    if not check_ssid(arg):
        return 12
    ssid = {"upri": {"ssid": arg}}
    write_role('wlan', ssid)

# return values:
# 11: password does not meet password policy


def action_set_password(arg):
    print 'setting password'
    if not check_passwd(arg):
        return 11
    passwd = {"upri": {"passwd": arg}}
    write_role('wlan', passwd)

#
# return values:
# 12: ssid does not meet policy
#


def action_set_tor_ssid(arg):
    print 'setting tor ssid to "%s"' % arg
    if not check_ssid(arg):
        return 12
    ssid = {"ninja": {"ssid": arg}}
    write_role('wlan', ssid)

# return values:
# 11: password does not meet password policy


def action_set_tor_password(arg):
    print 'setting tor password'
    if not check_passwd(arg):
        return 11
    passwd = {"ninja": {"passwd": arg}}
    write_role('wlan', passwd)


def action_restart_wlan(arg):
    print 'restarting wlan...'
    return call_ansible('ssid')

# return values:
# 10: invalid argument


def action_set_tor(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'tor enabled: %s' % arg
    tor = {"general": {"enabled": arg}}
    write_role('tor', tor)

# return values:
# 10: invalid argument


def action_set_silent(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'silent enabled: %s' % arg
    silent = {"general": {"enabled": arg}}
    write_role('wlan', silent)


def action_restart_tor(arg):
    print 'restarting tor...'
    return call_ansible('toggle_tor')


def action_restart_silent(arg):
    print 'restarting silent...'
    return call_ansible('toggle_silent')

# return values:
# 10: invalid argument


def action_set_vpn(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'vpn enabled: %s' % arg
    vpn = {"general": {"enabled": arg}}
    write_role('vpn', vpn)
    return 0

# return values:
# 10: invalid argument


def action_set_vpn_connection(arg):
    '1194/udp'
    port, protocol = arg.split('/')
    protocol = protocol.upper()
    if not int(port) in range(1025, 65535) or protocol not in ['UDP', 'TCP']:
        print 'error: only valid "port/protocol" combinations are allowed e.g. "1194/UDP"'
        print 'port must be unprivileged: 1025 - 65535'
        print 'protocol can be either UDP or TCP'
        return 10
    print 'vpn connection: %s' % arg
    vpn_connection = {"connection": {"port": port, "protocol": protocol}}
    write_role('vpn', vpn_connection)
    return 0

# return values:
# 10: invalid argument


def action_set_wlan_channel(arg):
    if not int(arg) in range(1, 10):
        print 'error: channel must be between 1 and 10'
        return 10
    print 'wifi channel: %s' % arg
    channel = {"general": {"channel": arg}}
    write_role('wlan', channel)
    return 0


def action_restart_vpn(arg):
    print 'restarting vpn...'
    # return 0 # TODO implement
    return call_ansible('toggle_vpn')

# return values:
# 10: invalid argument


def action_set_ssh(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'ssh enabled: %s' % arg
    en = {"general": {"enabled": arg}}
    write_role('ssh', en)


def action_restart_ssh(arg):
    print 'restarting ssh...'
    return call_ansible('toggle_ssh')

# return values:
# 10: invalid argument


def action_set_apate(arg):
    if arg not in ['yes', 'no']:
        print 'error: only "yes" and "no" are allowed'
        return 10
    print 'apate enabled: %s' % arg
    en = {"general": {"enabled": arg}}
    write_role('apate', en)


def action_restart_apate(arg):
    print 'restarting apate...'
    return call_ansible('toggle_apate')

def action_configure_devices(arg):
    print 'configuring devices...'
    return call_ansible('configure_devices')

def action_set_static_ip(arg):
    if arg not in ['dhcp', 'static']:
        print 'error: only "dhcp" and "static" are allowed'
        return 10
    print 'interface mode: %s' % arg
    en = {"general": {"mode": arg}}
    write_role('interfaces', en)


def check_passwd(arg):
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
    domain_value = domain.Domain(arg)
    if not domain_value.is_valid():
        if not domain_value.has_allowed_length():
            print 'the password can only contain up to 255 characters'
        if not domain_value.has_only_allowed_chars():
            print 'the domain must only contain following special characters: %s' % domain_value.get_allowed_chars()

        return False
    else:
        return True


def action_restart_firewall(arg):
    print 'restarting firewall...'
    return call_ansible('iptables')

# add your custom actions here
ALLOWED_ACTIONS = {
    'set_ssid': action_set_ssid,
    'set_password': action_set_password,
    'set_tor_ssid': action_set_tor_ssid,
    'set_tor_password': action_set_tor_password,
    'restart_wlan': action_restart_wlan,
    'enable_tor': action_set_tor,
    'enable_silent': action_set_silent,
    'restart_tor': action_restart_tor,
    'restart_silent': action_restart_silent,
    'enable_vpn': action_set_vpn,
    'set_vpn_connection': action_set_vpn_connection,
    'set_wlan_channel': action_set_wlan_channel,
    'restart_vpn': action_restart_vpn,
    'enable_ssh': action_set_ssh,
    'restart_ssh': action_restart_ssh,
    'enable_apate': action_set_apate,
    'enable_static_ip': action_set_static_ip,
    'restart_apate': action_restart_apate,
    'parse_logs': action_parse_logs,
    'parse_user_agents': action_parse_user_agents,
    'generate_profile': action_generate_profile,
    'delete_profile': action_delete_profile,
    'restart_firewall': action_restart_firewall,
    'enable_device': action_enable_device,
    'disable_device': action_disable_device,
    'set_ip': action_set_ip,
    'configure_devices': action_configure_devices,
    'set_dns_server': action_set_dns_server,
    'set_netmask': action_set_netmask,
    'set_gateway': action_set_gateway,
    'restart_network': action_restart_network,
    'set_dhcpd': action_set_dhcpd,
    'restart_dhcpd': action_restart_dhcpd,
}

#
# calls ansible and executes the given tag locally
#


def call_ansible(tag):
    return subprocess.call([ANSIBLE_COMMAND, '-i', ANSIBLE_INVENTORY, ANSIBLE_PLAY, "--tags", tag, "--connection=local"])

#
# write the custom json "data" to the fact with the given name "rolename"
#


def write_role(rolename, data):
    p = path.join(FACTS_DIR, rolename + '.fact')
    try:
        with open(p, 'r') as data_file:
            js = json.load(data_file)
    except IOError:
        js = {}

    js = merge(js, data)
    with open(p, 'w+') as data_file:
        json.dump(js, data_file, indent=4)

# return values:
# 0: ok
# 1: syntax error
# 2: invalid number of arguments
# 3: invalid action


def main():
    # append empty second parameter if none given
    if len(sys.argv) == 2:
        sys.argv.append('')

    if len(sys.argv) != 3:
        usage(2)

    action = sys.argv[1]
    args = sys.argv[2]

    # check if requested actions is valid
    if sys.argv[1] in ALLOWED_ACTIONS:
        print "action: %s" % action
        return ALLOWED_ACTIONS[action](args)
    else:
        usage(3)


def usage(ex):
    print "usage: %s <action> <args>" % sys.argv[0]
    print "allowed actions:"
    for action in ALLOWED_ACTIONS:
        print "    %s" % action
    exit(ex)


if __name__ == "__main__":
    exit(main())
