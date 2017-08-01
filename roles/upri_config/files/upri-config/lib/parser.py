import json
import subprocess
import re
from datetime import datetime
import time
from urlparse import urlparse
import os
import sqlite3
import redis as redisDB
from lib.settings import DEVICE_DEFAULT_MODE
from netaddr import EUI, IPAddress, AddrFormatError

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
                # conn = sqlite3.connect(dbfile)
                # c = conn.cursor()
                with sqlite3.connect(dbfile) as conn:
                    c = conn.cursor()
                    for line in squid:
                        # with conn:
                        parts = line.strip().split(";|;")

                        try:
                            EUI(parts[0])
                            IPAddress(parts[1])
                        except AddrFormatError:
                            continue
                        else:
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
                                c.execute("INSERT INTO devices_deviceentry (ip, mac, mode) VALUES (?, ?, ?)", (parts[1], parts[0], DEVICE_DEFAULT_MODE))
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

                # conn.close()
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
