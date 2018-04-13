import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from urlparse import urlparse

import redis as redisDB
from lib.settings import DEVICE_DEFAULT_MODE
from netaddr import EUI
from subprocess import check_output

redis = redisDB.StrictRedis(host="localhost", port=6379, db=7)

# syntax for keys in redis db for statistics
_DELIMITER = ":"
"""str: Delimiter used for separating parts of keys in the redis db."""
_PREFIX = _DELIMITER.join(("stats", "v2"))
"""str: Prefix which is used for every key in the redis db."""
_DNSMASQ = "dnsmasq"
_PRIVOXY = "privoxy"
_DEVICE = "device"
_BLOCKED = "blocked"
_QUERIED = "queried"
_WEEK = "week"
_DOMAIN = "domain"

# 6 weeks in seconds
_TTL = 3629000

#
# lookup MAC address associated with ip address
# return MAC address as EUI instance
#


def get_mac_from_ip(ip):
    arp_entry = check_output(["arp", "-n", ip])
    unix_mac = re.search(r"(([a-f\d]{1,2}\:){5}[a-f\d]{1,2})", arp_entry).groups()[0]
    mac = EUI(unix_mac)
    return mac


#
# parse the privoxy and dnsmasq logfiles and insert data into django db
# return values:
# 16: error
# 1: new entries have been added
# 0: no changes


def action_parse_logs(arg):
    with open('/etc/ansible/default_settings.json', 'r') as f:
        config = json.load(f)
    vals = [
        parse_dnsmasq_logs(
            os.path.join(config['log']['general']['path'], config['log']['dnsmasq']['subdir'], config['log']['dnsmasq']['logfiles']['logname'])
        ),
        #parse_dnsmasq_logs(
        #    os.path.
        #    join(config['log']['general']['path'], config['log']['dnsmasq_ninja']['logfiles']['logname'])
        #),
        parse_privoxy_logs(arg)
    ]
    if 16 in vals:
        return 16
    elif 1 in vals:
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

    logfile = os.path.join(config['log']['general']['path'], config['log']['privoxy']['subdir'], config['log']['privoxy']['logfiles']['logname'])

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
                        psite = urlparse(ssite).netloc

                        # calendar week
                        week = pdate.date().isocalendar()[1]

                        # filtered overall counter
                        redis.incr(_DELIMITER.join((_PREFIX, _PRIVOXY, _BLOCKED)))

                        # filtered counter per calendar week
                        redis.incr(_DELIMITER.join((_PREFIX, _PRIVOXY, _BLOCKED, _WEEK, str(week))))
                        redis.expire(_DELIMITER.join((_PREFIX, _PRIVOXY, _BLOCKED, _WEEK, str(week))), _TTL)

                        # store filtered domain count per week
                        redis.hincrby(_DELIMITER.join((_PREFIX, _PRIVOXY, _BLOCKED, _WEEK, str(week), _DOMAIN)), psite, 1)
                        redis.expire(_DELIMITER.join((_PREFIX, _PRIVOXY, _BLOCKED, _WEEK, str(week), _DOMAIN)), _TTL)

                        changed = True
                        print "found new block: [%s] %s" % (sdate, psite)
                except Exception as e:
                    print "failed to parse line \"%s\": %s" % (line, e.message)

        if changed:
            try:
                # truncate logfile
                with open(logfile, "a") as lf:
                    lf.truncate(0)
            except Exception as e:
                print "failed to write to redis database"
                return 16
            return 1
    else:
        print "failed to parse privoxy logfile %s: file not found" % logfile
        return 16

    return 0


def parse_blocked_domain(log_line, cur_year):
    blockedPattern = re.compile('([a-zA-Z]{3} ? \d{1,2} (\d{2}:?){3}) dnsmasq\[[0-9]*\]: config (.*) is 192.168.55.254')
    try:
        res = re.match(blockedPattern, log_line)
        if res:
            sdate = res.group(1)
            ssite = res.group(3)
            psite = str(ssite)
            pdate = datetime.strptime(sdate, '%b %d %H:%M:%S').replace(year=cur_year)

            # calendar week
            week = pdate.date().isocalendar()[1]

            # blocked overall counter
            redis.incr(_DELIMITER.join((_PREFIX, _DNSMASQ, _BLOCKED)))

            # filtered counter per calendar week
            redis.incr(_DELIMITER.join((_PREFIX, _DNSMASQ, _BLOCKED, _WEEK, str(week))))
            redis.expire(_DELIMITER.join((_PREFIX, _DNSMASQ, _BLOCKED, _WEEK, str(week))), _TTL)

            # store filtered domain count per week
            redis.hincrby(_DELIMITER.join((_PREFIX, _DNSMASQ, _BLOCKED, _WEEK, str(week), _DOMAIN)), psite, 1)
            redis.expire(_DELIMITER.join((_PREFIX, _DNSMASQ, _BLOCKED, _WEEK, str(week), _DOMAIN)), _TTL)

            #print "found new blocked query: [%s] %s" % (psite, pdate)
            return True
    except Exception as e:
        print "failed to parse blocked query \"%s\": %s" % (log_line, e.message)
        return False

#
# parse dnsmasq dns query line
#


def parse_dns_query(log_line, cur_year):
    queryPattern = re.compile(
        '(.*) dnsmasq\[[0-9]*\]: query\[[A-Z]*\] (.*) from (.*)')
    try:
        res = re.match(queryPattern, log_line)
        if res:
            sdate = res.group(1)
            ssite = res.group(2)
            sip = res.group(3)

            psite = str(ssite)
            pdate = datetime.strptime(sdate, '%b %d %H:%M:%S').replace(year=cur_year)

            try:
                mac = get_mac_from_ip(sip)
            except AttributeError:
                #print "No MAC found for {}".format(sip)
                return False

            # calendar week
            week = pdate.date().isocalendar()[1]

            # store filtered domain count per week
            redis.hincrby(_DELIMITER.join((_PREFIX, _DEVICE, _QUERIED, str(mac), _WEEK, str(week), _DOMAIN)), psite, 1)
            redis.expire(_DELIMITER.join((_PREFIX, _DEVICE, _QUERIED, str(mac), _WEEK, str(week), _DOMAIN)), _TTL)

            #print "found device query: %s from %s at %s " % (psite, mac, pdate)
            return True
    except Exception as e:
        print "failed to parse device query \"%s\": %s" % (log_line, e.message)
        return False


#
# parse the dnsmasq logfile and insert data into redis db
# return values:
# 16: error
# 1: new entries have been added
# 0: no changes
def parse_dnsmasq_logs(arg):
    logfile = arg

    if os.path.isfile(logfile):

        print "parsing dnsmasq logfile %s" % logfile
        cur_year = time.localtime().tm_year
        block_count = block_count_failed = query_count = query_count_failed = 0

        with open(logfile, 'r+') as dnsmasq:
            for line in dnsmasq:
                if line.strip().endswith('192.168.55.254'):
                    if parse_blocked_domain(line, cur_year): block_count += 1
                    else: block_count_failed += 1
                elif ' query' in line \
                        and not line.strip().endswith('127.0.0.1'):
                    if parse_dns_query(line, cur_year): query_count += 1
                    else: query_count_failed += 1

            print "Found {} device queries ({} failed) and {} blocked queries ({} failed)"\
                .format(query_count, query_count_failed, block_count, block_count_failed)
            try:
                dnsmasq.truncate(0)
                if block_count > 0 or query_count > 0:
                    return 1
                else:
                    return 0
            except Exception as error:
                print "Failed to truncate file: {}".format(error)
            return 16

    else:
        print "failed to parse dnsmasq logfile %s: file not found" % logfile
        return 16

    return 0


#
# parse the squid logfile and insert new user-agents into redis db
# return values:
# 16: error
# 1: new entries have been added
# 0: no changes


def action_parse_user_agents(arg):
    sys.path.insert(0, "/opt/registrar/lib/")
    from util import check_preconditions
    errors = False

    with open('/etc/ansible/default_settings.json', 'r') as f:
        config = json.load(f)

    dbfile = config['django']['db']
    logfile = os.path.join(config['log']['general']['path'], config['log']['squid']['subdir'], config['log']['squid']['logfiles']['logname'])

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
                        timestamp = None
                        try:
                            timestamp = datetime.fromtimestamp(float(parts[3]))
                        except (ValueError, IndexError):
                            timestamp = datetime.now()

                        # try:
                        #     EUI(parts[0])
                        #     IPAddress(parts[1])
                        # except AddrFormatError:
                        #     continue

                        if not check_preconditions(parts[1], parts[0]):
                            continue
                        else:
                            agent_id = None
                            try:
                                c.execute("INSERT INTO devices_useragent (agent) VALUES (?)", (parts[2], ))
                                agent_id = c.lastrowid
                            except sqlite3.IntegrityError as sqlie:
                                if "UNIQUE constraint failed: devices_useragent.agent" in sqlie.message:
                                    c.execute("SELECT id FROM devices_useragent WHERE agent=?", (parts[2], ))
                                    try:
                                        agent_id = c.fetchone()[0]
                                    except (TypeError, IndexError):
                                        raise ValueError("Unable to retrieve id of useragent string")
                                else:
                                    raise sqlie

                            device_id = None
                            try:
                                c.execute(
                                    "INSERT INTO devices_deviceentry (ip, mac, mode, last_seen) VALUES (?, ?, ?, ?)",
                                    (parts[1], parts[0], DEVICE_DEFAULT_MODE, timestamp)
                                )
                                device_id = c.lastrowid
                            except sqlite3.IntegrityError as sqlie:
                                if "UNIQUE constraint failed: devices_deviceentry.mac" in sqlie.message:
                                    c.execute("SELECT id, ip, last_seen from devices_deviceentry where mac=?", (parts[0], ))
                                    res = c.fetchone()
                                    if not res:
                                        raise ValueError("Unable to retrieve id of device")

                                    device_id = res[0]
                                    # res[1] != parts[1] or
                                    entry_date = None
                                    try:
                                        entry_date = datetime.strptime(res[2], "%Y-%m-%d %H:%M:%S.%f")
                                    except ValueError:
                                        entry_date = datetime.strptime(res[2], "%Y-%m-%d %H:%M:%S")

                                    if timestamp > entry_date:
                                        c.execute("UPDATE devices_deviceentry SET ip=?, last_seen=? where mac=?", (parts[1], timestamp, parts[0]))
                                else:
                                    raise sqlie

                            try:
                                if agent_id is not None and device_id is not None:
                                    c.execute(
                                        "INSERT INTO devices_deviceentry_user_agent (deviceentry_id, useragent_id) values (?, ?)",
                                        (str(device_id), str(agent_id))
                                    )
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

            rc = subprocess.call(
                [
                    "/var/webapp-virtualenv/bin/python", "/usr/share/nginx/www-upri-interface/manage.py", "fingerprint", "--settings",
                    config['django']['settings']
                ]
            )
            if rc != 0:
                print "user agent parsing failed"
                return 16

            return 1
    else:
        print "failed to parse squid logfile %s: file not found" % logfile
        return 16

    return 0
