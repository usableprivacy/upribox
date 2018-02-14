# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date, datetime, time

from devices.models import DeviceEntry
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from lib.stats import get_week_days
from lib.utils import human_format

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

    for date in get_week_days(year, week):
        traffic = device_day_stats(date, dev.ip, metric=Metric.CATEGORIES)
        days.append({
            'year': date.year,
            'month': date.month,
            'day': date.day,
            'traffic': traffic,
        })

        total += sum(traffic.values())

    stats = {
        'total': human_format(total, binary=True, suffix='B'),
        'days': days,
        'calendarweek': week,
    }

    return JsonResponse(stats, safe=False)
