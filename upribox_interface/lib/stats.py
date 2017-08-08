# -*- coding: utf-8 -*-
import logging
import operator
from datetime import date, datetime, timedelta

import redis as redisDB
from django.conf import settings

logger = logging.getLogger('uprilogger')

redis = redisDB.StrictRedis(host=settings.REDIS['HOST'], port=settings.REDIS['PORT'], db=settings.REDIS['DB'])

# syntax for keys in redis db for statistics
_DELIMITER = ":"
"""str: Delimiter used for separating parts of keys in the redis db."""
_PREFIX = _DELIMITER.join(("stats", "v2"))
"""str: Prefix which is used for every key in the redis db."""
_DNSMASQ = "dnsmasq"
_PRIVOXY = "privoxy"
_BLOCKED = "blocked"
_WEEK = "week"
_DOMAIN = "domain"


# return overall counter tuple(filtered, blocked)
def get_overall_counters():
    return (
        redis.get(_DELIMITER.join((_PREFIX, _PRIVOXY, _BLOCKED))),
        redis.get(_DELIMITER.join((_PREFIX, _DNSMASQ, _BLOCKED))),
    )


# week number
# return week counter tuple(filtered, blocked)
def get_week_counters(week):
    return (
        redis.get(_DELIMITER.join((_PREFIX, _PRIVOXY, _BLOCKED, _WEEK, str(week)))) or 0,
        redis.get(_DELIMITER.join((_PREFIX, _DNSMASQ, _BLOCKED, _WEEK, str(week)))) or 0,
    )


def week_exists(week):
    try:
        return sum(int(entry) for entry in get_week_counters(week)) > 0
    except ValueError:
        return False


# limit only when sorted
def get_domains(week, sort=False, limit=None):
    filtered, blocked = get_domain_counters(week, sort, limit)

    return (filtered.keys(), blocked.keys())
    # else:
    #     return (
    #         [entry[0] for entry in filtered],
    #         [entry[0] for entry in blocked],
    #     )


# limit only when sorted
def get_domain_counters(week, sort=False, limit=None):
    filtered = redis.hgetall(_DELIMITER.join((_PREFIX, _PRIVOXY, _BLOCKED, _WEEK, str(week), _DOMAIN)))
    blocked = redis.hgetall(_DELIMITER.join((_PREFIX, _DNSMASQ, _BLOCKED, _WEEK, str(week), _DOMAIN)))

    if not sort:
        return (filtered, blocked)
    else:
        return (
            dict(sorted(filtered.items(), key=operator.itemgetter(1), reverse=True)[:limit]),
            dict(sorted(blocked.items(), key=operator.itemgetter(1), reverse=True)[:limit]),
        )


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
