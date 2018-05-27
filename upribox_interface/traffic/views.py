# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import date, datetime, time

from devices.models import DeviceEntry
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from lib.stats import get_week_days, get_queries_for_device
from lib.utils import human_format, exec_upri_config
from colour import Color
from lib import jobs

from .ntopng import Metric, device_day_stats

# Get an instance of a logger
logger = logging.getLogger('uprilogger')


@require_http_methods(["GET", "POST"])
@login_required
def get_statistics(request, slug, week=None, year=None):
    dev = None
    try:
        if not (week and year):
            year, week, __ = datetime.now().date().isocalendar()
        else:
            # check if week and year are valid
            datetime.strptime(week + '-' + year, '%W-%Y')

            # do not use resulting date because of something like this:
            # datetime.datetime.strptime("01:2016", '%W:%Y').isocalendar()
            # (2015, 53, 5)
            year = int(year)
            week = int(week)
            if week == 0:
                raise ValueError()

        dev = DeviceEntry.objects.get(slug=slug)

    except (ValueError, TypeError, DeviceEntry.DoesNotExist):
        return HttpResponse(status=412)

    days = []
    total = 0
    from collections import Counter
    total_protocols = Counter()

    for date in get_week_days(year, week):
        traffic = device_day_stats(date, dev.ip, sent_recv=False, metric=Metric.PROTOCOLS)
        #traffic = device_day_stats(date, dev.ip, metric=Metric.CATEGORIES)
        days.append({
#            'year': date.year,
#            'month': date.month,
#            'day': date.day,
            'date': date.strftime('%Y-%m-%d'),
            'traffic': traffic,
        })

        total += sum(traffic.values())
        total_protocols.update(traffic)

    protocols_top = sorted(total_protocols, key=total_protocols.get, reverse=True)
    if len(protocols_top) > 0:
        colors = list(Color('#47ADC0').range_to(Color('black'), len(protocols_top)))

    protocols = list()

    for protocol in protocols_top:
        dates = list()
        amounts = list()
        for day in days:
            dates.append(day['date'])
            if protocol in day['traffic']:
                amounts.append(day['traffic'][protocol])
            else:
                amounts.append(0.0)
        protocols.append({'protocol': protocol, 'color': colors[protocols_top.index(protocol)].hex,
                          'dates': dates, 'amounts': amounts})
    protocols.reverse()

    stats = {
        'total': human_format(total*1024*1024, binary=True, suffix='B'),
        'protocols': protocols,
        'days': days,
        'calendarweek': week,
    }

    return JsonResponse(stats, safe=False)


@require_http_methods(["GET", "POST"])
@login_required
def get_overview(request, slug):
    return render(
        request, "overview.html", {"device": DeviceEntry.objects.get(slug=slug)}
    )


@require_http_methods(["GET", "POST"])
@login_required
def get_device_queries(request, slug, week=None):
    if not week:
        week = datetime.now().date().isocalendar()[1]
        week = int(week)

    try:
        logger.debug("parsing logs")
        exec_upri_config('parse_logs')
        if int(week) == 0:
            raise ValueError()
    except (ValueError, TypeError) as error:
        return HttpResponse(status=412)

    try:

        dev = DeviceEntry.objects.get(slug=slug)
        domains = get_queries_for_device(dev.mac, week, sort=True, limit=10)

    except (ValueError, TypeError, DeviceEntry.DoesNotExist) as error:
        #return JsonResponse(error, safe=False)
        return HttpResponse(status=412)

    return JsonResponse({'domains': domains})
