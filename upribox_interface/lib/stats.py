# -*- coding: utf-8 -*-
import logging
import operator
from datetime import date, datetime, timedelta

import redis as redisDB
from django.conf import settings
from netaddr import EUI

logger = logging.getLogger('uprilogger')

redis = redisDB.StrictRedis(host=settings.REDIS['HOST'], port=settings.REDIS['PORT'], db=settings.REDIS['DB'])

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

# return overall counter tuple(filtered, blocked)
def get_overall_counters():
    return (
        redis.get(_DELIMITER.join((_PREFIX, _PRIVOXY, _BLOCKED))) or '0',
        redis.get(_DELIMITER.join((_PREFIX, _DNSMASQ, _BLOCKED))) or '0',
    )


# week number
# return week counter tuple(filtered, blocked)
def get_week_counters(week):
    return (
        redis.get(_DELIMITER.join((_PREFIX, _PRIVOXY, _BLOCKED, _WEEK, str(week)))) or '0',
        redis.get(_DELIMITER.join((_PREFIX, _DNSMASQ, _BLOCKED, _WEEK, str(week)))) or '0',
    )


def week_exists(week):
    try:
        return sum(int(entry) for entry in get_week_counters(week)) > 0
    except ValueError:
        return False


# limit only when sorted
def get_domains(week, sort=False, limit=None):
    filtered, blocked = get_domain_counters(week, sort, limit)
    # return (filtered.keys(), blocked.keys())
    # else:
    return (
        [entry[0] for entry in filtered],
        [entry[0] for entry in blocked],
    )


# limit only when sorted
def get_domain_counters(week, sort=False, limit=None):
    filtered = redis.hgetall(_DELIMITER.join((_PREFIX, _PRIVOXY, _BLOCKED, _WEEK, str(week), _DOMAIN)))
    blocked = redis.hgetall(_DELIMITER.join((_PREFIX, _DNSMASQ, _BLOCKED, _WEEK, str(week), _DOMAIN)))

    if not sort:
        return (filtered.items(), blocked.items())
    else:
        return (
            sorted(filtered.items(), cmp=lambda x, y: int(x) - int(y), key=operator.itemgetter(1), reverse=True)[:limit],
            sorted(blocked.items(), cmp=lambda x, y: int(x) - int(y), key=operator.itemgetter(1), reverse=True)[:limit],
        )


# limit only when sorted
def get_queries_for_device(mac, week, sort=False, limit=None):

    device_queries = redis.hgetall(_DELIMITER.join((_PREFIX, _DEVICE, _QUERIED, str(EUI(mac)), _WEEK, str(week), _DOMAIN)))
    blocked = redis.hgetall(_DELIMITER.join((_PREFIX, _DNSMASQ, _BLOCKED, _WEEK, str(week), _DOMAIN)))
    blocked_queries = list()
    queries = list()

    if sort:
        device_queries = sorted(device_queries.items(), cmp=lambda x, y: int(x) - int(y), key=operator.itemgetter(1), reverse=True)
    else:
        device_queries = device_queries.items()

    for domain, count in device_queries:
        if domain in blocked:
            blocked_queries.append([domain, count])
        else:
            queries.append([domain, count])

    if len(blocked_queries) > 0:
        block_percent = round((sum(float(query[1]) for query in blocked_queries) / (sum(float(query[1]) for query in device_queries))) * 100.00, 2)
    else:
        block_percent = 0

    return queries[:limit], blocked_queries[:limit], block_percent


def sub_week(week, year, sub):
    try:
        return (tofirstdayinisoweek(year, week) - timedelta(days=7 * sub)).date().isocalendar()[1]
    except ValueError:
        return None


def tofirstdayinisoweek(year, week):
    ret = datetime.strptime('%04d-%02d-1' % (year, week), '%Y-%W-%w')
    if date(year, 1, 4).isoweekday() > 4:
        ret -= timedelta(days=7)
    return ret


def get_week_days(year, week):
    d = date(year, 1, 1)
    if (d.weekday() > 3):
        d = d + timedelta(7 - d.weekday())
    else:
        d = d - timedelta(d.weekday())
    dlt = timedelta(days=(week - 1) * 7)
    # return d + dlt, d + dlt + timedelta(days=6)
    return [d + dlt + timedelta(days=i) for i in range(7)]
