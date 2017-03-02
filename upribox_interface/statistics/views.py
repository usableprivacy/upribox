from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from lib import jobs
import lib.utils as utils
from django.http import HttpResponse
import json
from .models import PrivoxyLogEntry, DnsmasqQueryLogEntry, DnsmasqBlockedLogEntry
from datetime import datetime, time
from django.db import connection
from django.db.models import Sum, Count
from django.template.defaultfilters import date as _localdate
import time
import logging
from django.shortcuts import render
import redis as redisDB

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
__SIXMONTHS = "sixmonths"
__TODAY = "today"
__MONTHS = "months"
__DOMAINS = "domains"

"""
-- donuts --
(sum of stats:dnsmasq:blocked:months:*)
sum of stats:dnsmasq:adfree:months:*
stats:dnsmasq:blocked:(todaydate)
stats:dnsmasq:adfree:(todaydate)

-- bars --
stats:dnsmasq:blocked:months:1 - stats:dnsmasq:months:12
stats:privoxy:months:1 - stats:privoxy:months:12

-- lists --
stats:dnsmasq:blocked:domains:*
stats:privoxy:domains:*
"""

# Get an instance of a logger
logger = logging.getLogger(__name__)

@login_required
def get_statistics(request):
    return render_to_response("statistics.html", {
        "request": request,
        'messagestore': jobs.get_messages()
    })

@login_required()
def json_statistics(request):

    logger.debug("parsing logs")
    utils.exec_upri_config('parse_logs')

    # bar chart
    monthly = [[0]*5, [0]*5]

    now = time.localtime()
    months = [_localdate(datetime.fromtimestamp(time.mktime((now.tm_year, now.tm_mon - n, 1, 0, 0, 0, 0, 0, 0))),"F") for n in reversed(range(5))]
    months_nr = [_localdate(datetime.fromtimestamp(time.mktime((now.tm_year, now.tm_mon - n, 1, 0, 0, 0, 0, 0, 0))), "n") for n in reversed(range(5))]

    for i in range(5):
        dnsmasq_key = __DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, __MONTHS, str(months_nr[i])))
        monthly[0][i] = int(redis.get(dnsmasq_key) or 0)

        privoxy_key = __DELIMITER.join((__PREFIX, __PRIVOXY, __MONTHS, str(months_nr[i])))
        monthly[1][i] = int(redis.get(privoxy_key) or 0)

    # lists
    all_filtered_pages = list()
    for key in redis.scan_iter(__DELIMITER.join((__PREFIX, __PRIVOXY, __DOMAINS, "*"))):
        site = key.replace(__DELIMITER.join((__PREFIX, __PRIVOXY, __DOMAINS)) + ":", "")
        all_filtered_pages.append({"url": site, "count": int(redis.get(key) or 0)})
    filtered_pages = sorted(all_filtered_pages, key=lambda k: k['count'], reverse=True)[:5]

    all_blocked_pages = list()
    for key in redis.scan_iter(__DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, __DOMAINS, "*"))):
        site = key.replace(__DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, __DOMAINS)) + ":", "")
        all_blocked_pages.append({"url": site, "count": int(redis.get(key) or 0)})
    blocked_pages = sorted(all_blocked_pages, key=lambda k: k['count'], reverse=True)[:5]

    # pi charts
    sum_adfree_sixmonths = 0
    sum_blocked_sixmonths = 0
    for i in range(5):
        blocked_key = __DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, __MONTHS, str(months_nr[i])))
        sum_blocked_sixmonths += int(redis.get(blocked_key) or 0)
        adfree_key = __DELIMITER.join((__PREFIX, __DNSMASQ, __ADFREE, __MONTHS, str(months_nr[i])))
        sum_adfree_sixmonths += int(redis.get(adfree_key) or 0)


    today = datetime.now().date().strftime('%Y-%m-%d')
    # return 0 if key does not exist
    sum_blocked_today = int(redis.get(__DELIMITER.join((__PREFIX, __DNSMASQ, __BLOCKED, today))) or 0)
    sum_adfree_today = int(redis.get(__DELIMITER.join((__PREFIX, __DNSMASQ, __ADFREE, today))) or 0)

    pie1_data = [sum_adfree_sixmonths, sum_blocked_sixmonths]
    pie2_data = [sum_adfree_today, sum_blocked_today]

    return HttpResponse(json.dumps({'pie1_data': {
                                        'series': pie1_data
                                    },
                                    'pie2_data': {
                                        'series': pie2_data
                                    },
                                    'filtered_pages': filtered_pages,
                                    'blocked_pages': blocked_pages,
                                    'bar_data': {
                                        'labels': months,
                                        'series': monthly
                                    }}),  content_type="application/json")