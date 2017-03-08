#!/usr/bin/env python
# coding=utf-8
from django.core.management.base import NoArgsCommand
from statistics.models import PrivoxyLogEntry, DnsmasqBlockedLogEntry, DnsmasqQueryLogEntry
from django.utils import timezone
from django.template.defaultfilters import date as _localdate
import redis as redisDB
from datetime import datetime as dt
import time
import json
import sqlite3

#
# transfer the old statistics from the sqlite db to the new accumulated redis db
# delete monthly data that is older than 6 months
# delete daily data that is not from today
#
class Command(NoArgsCommand):
    def handle_noargs(self, **options):

        redis = redisDB.StrictRedis(host="localhost", port=6379, db=7)

        with open('/etc/ansible/default_settings.json', 'r') as f:
            config = json.load(f)

        dbfile = config['django']['db']

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

        """
        -- donuts --
        (sum of stats:dnsmasq:blocked:month:*)
        sum of stats:dnsmasq:adfree:month:*
        stats:dnsmasq:blocked:day:(todaydate)
        stats:dnsmasq:adfree:day:(todaydate)

        -- bars --
        stats:dnsmasq:blocked:month:1 - stats:dnsmasq:blocked:month:12
        stats:privoxy:blocked:month:1 - stats:privoxy:blocked:month:12

        -- lists --
        stats:dnsmasq:blocked:domain:*
        stats:privoxy:blocked:domain:*
        """

        today = timezone.now().date().strftime('%Y-%m-%d')
        now = time.localtime()
        months_nr = [_localdate(dt.fromtimestamp(time.mktime((now.tm_year, now.tm_mon - n, 1, 0, 0, 0, 0, 0, 0))), "n")
                     for n in reversed(range(6))]
        outdated_months = [
            _localdate(dt.fromtimestamp(time.mktime((now.tm_year, now.tm_mon - n - 6, 1, 0, 0, 0, 0, 0, 0))), "n") for n
            in reversed(range(6))]
        oldest_valid_day = timezone.make_aware(dt.fromtimestamp(time.mktime((now.tm_year, now.tm_mon - 5, 1, 0, 0, 0, 0, 0, 0))), timezone.get_current_timezone())
        print "today: " + today
        print "month_nr: " + str(months_nr)
        print "outdated_months: " + str(outdated_months)
        print "oldest_valid_day: " + str(oldest_valid_day)

        # delete outdated months from redis db
        for month in outdated_months:
            redis.set(__DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, __MONTH, month)), "0")
            redis.set(__DELIMITER.join((__PREFIX, __DNSMASQ, __ADFREE, __MONTH, month)), "0")
            redis.set(__DELIMITER.join((__PREFIX, __PRIVOXY, __BLOCKED, __MONTH, month)), "0")
            print "deleted outdated month " + str(month)

        # delete outdated days from redis db
        for key in redis.scan_iter(__DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, __DAY, "*"))):
            date = key.replace(__DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, __DAY)) + ":", "")
            if date != today:
                redis.delete(key)
                print "deleted outdated day for dnsblocked " + date

        for key in redis.scan_iter(__DELIMITER.join((__PREFIX, __DNSMASQ, __ADFREE, __DAY, "*"))):
            date = key.replace(__DELIMITER.join((__PREFIX, __DNSMASQ, __ADFREE, __DAY)) + ":", "")
            if date != today:
                redis.delete(key)
                print "deleted outdated day for dns adfree " + date

        # transfer PrivoxyLogEntries to redis db
        for privoxy_entry in PrivoxyLogEntry.objects.all().iterator():
            if privoxy_entry.log_date >= oldest_valid_day:
                month = privoxy_entry.log_date.month
                if str(month) in months_nr:
                    redis.incr(__DELIMITER.join((__PREFIX, __PRIVOXY, __BLOCKED, __MONTH, str(month))))
                    print "incr priv month " + str(month)
            redis.incr(__DELIMITER.join((__PREFIX, __PRIVOXY, __BLOCKED, __DOMAIN, privoxy_entry.url)))
            print "incr priv domain " + privoxy_entry.url

        # transfer DnsmasqBlockedLogEntries to redis db
        for dnsmasq_blocked_entry in DnsmasqBlockedLogEntry.objects.all().iterator():
            if dnsmasq_blocked_entry.log_date >= oldest_valid_day:
                pdate = dnsmasq_blocked_entry.log_date.strftime('%Y-%m-%d')
                month = dnsmasq_blocked_entry.log_date.month
                if pdate == today:
                    redis.incr(__DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, today)))
                    print "incr dns blocked day " + str(today)
                if str(month) in months_nr:
                    redis.incr(__DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, __MONTH, str(month))))
                    print "incr dns blocked month " + str(month)
            redis.incr(__DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, __DOMAIN, dnsmasq_blocked_entry.url)))
            print "incr dns blocked domain " + dnsmasq_blocked_entry.url

        # transfer DnsmasqQueryLogEntries to redis db
        for dnsmasq_query_entry in DnsmasqQueryLogEntry.objects.all().iterator():
            if dnsmasq_query_entry.log_date >= oldest_valid_day:
                pdate = dnsmasq_query_entry.log_date.strftime('%Y-%m-%d')
                month = dnsmasq_query_entry.log_date.month
                if pdate == today:
                    redis.incr(__DELIMITER.join((__PREFIX, __DNSMASQ, __ADFREE, __DAY, today)))
                    print "incr dns adfree day " + str(today)
                if str(month) in months_nr:
                    redis.incr(__DELIMITER.join((__PREFIX, __DNSMASQ, __ADFREE, __MONTH, str(month))))
                    print "incr dns adfree month " + str(month)

        try:
            conn = sqlite3.connect(dbfile)
            c = conn.cursor()
            c.execute("DELETE FROM statistics_dnsmasqquerylogentry")
            print "del dnsmasqquery"
            c.execute("DELETE FROM statistics_dnsmasqblockedlogentry")
            print "del dnsmasqblocked"
            c.execute("DELETE FROM statistics_privoxylogentry")
            print "del privoxylog"
            conn.execute("VACUUM")
            print "vacuum"
            conn.commit()
            conn.close()
        except Exception as e:
            print "failed to write to database"