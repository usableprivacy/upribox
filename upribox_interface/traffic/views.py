# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date, datetime, time

from devices.models import DeviceEntry
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from lib.stats import get_week_days
from lib.utils import human_format
from colour import Color
from lib import jobs

from .ntopng import Metric, device_day_stats


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
    protocols = list()
    colors = list(Color('#47ADC0').range_to(Color('black'), len(protocols_top)))
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
