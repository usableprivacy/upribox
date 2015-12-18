from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from lib import jobs
from django.http import HttpResponse
import json
from .models import PrivoxyLogEntry
from datetime import datetime
from django.db import connection
from django.db.models import Sum, Count
from django.template.defaultfilters import date as _localdate
import time

@login_required
def get_statistics(request):
    return render_to_response("statistics.html", {
        "request": request,
        'messagestore': jobs.get_messages()
    })

@login_required()
def json_statistics(request):

    truncate_date = connection.ops.date_trunc_sql('month', 'log_date')
    qs = PrivoxyLogEntry.objects.extra({'month':truncate_date})
    log = qs.values('month').annotate(Count('pk')).order_by('month')
    monthly = [0]*5

    now = time.localtime()
    months = [_localdate(datetime.fromtimestamp(time.mktime((now.tm_year, now.tm_mon - n, 1, 0, 0, 0, 0, 0, 0))),"F") for n in reversed(range(5))]
    for entry in log:
        cur_month = _localdate(datetime.strptime(entry['month'], '%Y-%m-%d'), "F")
        monthly[months.index(cur_month)] = entry['pk__count']

    log = PrivoxyLogEntry.objects.values('url').annotate(Count('pk')).order_by('-pk__count')
    blocked_pages = list()

    for entry in log[0:5]:
        print entry
        blocked_pages.append({"url": entry['url'], "count": entry['pk__count']})

    return HttpResponse(json.dumps({'blocked_sites': blocked_pages, 'data': { 'labels': months, 'series':[ monthly ] }}),  content_type="application/json")
