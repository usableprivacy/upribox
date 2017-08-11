# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime, time

import lib.utils as utils
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from lib import jobs, stats

SHOW_WEEKS = 5

# Get an instance of a logger
logger = logging.getLogger('uprilogger')


@login_required
def get_statistics(request):
    return render(request, "statistics.html", {'messagestore': jobs.get_messages()})


@login_required()
def json_statistics(request):

    logger.debug("parsing logs")
    utils.exec_upri_config('parse_logs')
    cur_week = datetime.now().date().isocalendar()[1]
    cur_year = datetime.now().year

    data = [
        {
            "week": stats.sub_week(cur_week, cur_year, i),
            "ugly": stats.get_week_counters(stats.sub_week(cur_week, cur_year, i))[0],
            "bad": stats.get_week_counters(stats.sub_week(cur_week, cur_year, i))[1]
        } for i in range(1, SHOW_WEEKS) if stats.week_exists(stats.sub_week(cur_week, cur_year, i))
    ]

    detailed = detailed_week(cur_week)

    data.insert(0, detailed)

    return JsonResponse(data, safe=False)


def detailed_week(week):
    filtered, blocked = stats.get_overall_counters()
    filtered_domains, blocked_domains = stats.get_domain_counters(week, sort=True, limit=5)

    detailed = {
        "week": week,
        "filtered": {
            "bad": blocked_domains,
            "ugly": filtered_domains
        },
        "overallCount": {
            "bad": blocked,
            "ugly": filtered
        },
    }
    return detailed


@login_required()
def statistics_update(request, week=None):
    if not week:
        week = datetime.now().date().isocalendar()[1]
    try:
        datetime.strptime(week, '%W')
        logger.debug("parsing logs")
        utils.exec_upri_config('parse_logs')
        if int(week) == 0:
            raise ValueError()
    except (ValueError, TypeError):
        return HttpResponse(status=412)

    return JsonResponse(detailed_week(week))
