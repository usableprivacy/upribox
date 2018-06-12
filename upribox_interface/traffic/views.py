# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime
from devices.models import DeviceEntry
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from lib.stats import get_queries_for_device
from lib.utils import human_format, exec_upri_config
from traffic.utils import get_weekly_traffic, get_protocols_by_volume


# Get an instance of a logger
logger = logging.getLogger('uprilogger')


@require_http_methods(["GET", "POST"])
@login_required
def get_statistics(request, slug, week=None, year=None):

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

    try:
        days, total, colors, texts, protocols_sorted = get_weekly_traffic(year, week, dev.ip)
    except Exception as error:
        return HttpResponse(status=412)
        #return HttpResponse(str(error))

    try:
        protocols = get_protocols_by_volume(days, protocols_sorted, colors)
    except Exception as error:
        return HttpResponse(status=412)
        #return HttpResponse(str(error))

    stats = {
        'total': human_format(total*1024*1024, binary=True, suffix='B'),
        'protocols': protocols,
        'days': days,
        'calendarweek': week,
        'year': year,
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
        domains, blocked_domains, block_percent = get_queries_for_device(dev.mac, week, sort=True, limit=10)

    except (ValueError, TypeError, DeviceEntry.DoesNotExist) as error:
        #return HttpResponse(error)
        return HttpResponse(status=412)

    return JsonResponse({'domains': domains, 'blocked_domains': blocked_domains, 'block_percent': block_percent})
