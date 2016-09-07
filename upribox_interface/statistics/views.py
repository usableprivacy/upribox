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


    truncate_date = connection.ops.date_trunc_sql('month', 'log_date')
    privoxy_qs = PrivoxyLogEntry.objects.extra({'month':truncate_date})
    privoxy_log = privoxy_qs.values('month').annotate(Count('pk')).order_by('month')
    dnsmasq_qs = DnsmasqBlockedLogEntry.objects.extra({'month': truncate_date})
    dnsmasq_log = dnsmasq_qs.values('month').annotate(Count('pk')).order_by('month')

    monthly = [[0]*5, [0]*5]

    now = time.localtime()
    months = [_localdate(datetime.fromtimestamp(time.mktime((now.tm_year, now.tm_mon - n, 1, 0, 0, 0, 0, 0, 0))),"F") for n in reversed(range(5))]
    for entry in privoxy_log:
        cur_month = _localdate(datetime.strptime(entry['month'], '%Y-%m-%d'), "F")
        monthly[1][months.index(cur_month)] = entry['pk__count']
    for entry in dnsmasq_log:
        cur_month = _localdate(datetime.strptime(entry['month'], '%Y-%m-%d'), "F")
        monthly[0][months.index(cur_month)] = entry['pk__count']


    privoxy_log = PrivoxyLogEntry.objects.values('url').annotate(Count('pk')).order_by('-pk__count')
    filtered_pages = list()
    dnsmasq_log = DnsmasqBlockedLogEntry.objects.values('url').annotate(Count('pk')).order_by('-pk__count')
    blocked_pages = list()

    for entry in privoxy_log[0:5]:
        #print entry
        filtered_pages.append({"url": entry['url'], "count": entry['pk__count']})
    for entry in dnsmasq_log[0:5]:
        #print entry
        blocked_pages.append({"url": entry['url'], "count": entry['pk__count']})

    today = datetime.now().date()
    total_blocked_queries = DnsmasqBlockedLogEntry.objects.count()
    today_blocked_queries = DnsmasqBlockedLogEntry.objects.filter(log_date__contains=today).count()
    pie1_data = [DnsmasqQueryLogEntry.objects.count() - total_blocked_queries, total_blocked_queries]
    pie2_data = [DnsmasqQueryLogEntry.objects.filter(log_date__contains=today).count() - today_blocked_queries, today_blocked_queries]

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