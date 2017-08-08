# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import time

import redis as redisDB
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from lib import info, jobs, utils
from more import jobs as morejobs

logger = logging.getLogger('uprilogger')


@login_required
@require_http_methods(["GET", "POST"])
def setup_init(request):
    phase = "init"
    context = {}

    if not info.check_ipv6():
        if info.check_connection():
            if request.method == 'GET' and utils.get_fact('apate', 'general', 'enabled') == 'no':
                jobs.queue_job(morejobs.toggle_apate, ("yes", ), unique=True)
                # context.update({'message': True})
        else:
            phase = "isolated"

    if info.check_ipv6():
        return redirect('upri_setup_failed')
    else:
        context.update(
            {
                'phase': phase,  # init, failed, success
                'refresh_url': reverse('upri_setup_eval'),
                'error_url': reverse('upri_setup_error')
            }
        )
        return render(request, "setup.html", context)


@login_required
@require_http_methods(["GET"])
def setup_eval(request):
    context = {'phase': "eval"}

    return render(request, "setup.html", context)


@login_required
@require_http_methods(["GET"])
def setup_error(request):
    return render(request, "setup.html")


@login_required
@require_http_methods(["GET", "POST"])
def setup_success(request):
    phase = "success"
    context = {}

    _setup_redis(phase)

    context.update({
        'phase': phase  # init, failed, success
    })
    return render(request, "setup.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def setup_failed(request):
    phase = "failed"
    context = {}

    _setup_redis(phase)

    if not info.check_ipv6():
        if request.method == 'GET' and utils.get_fact('apate', 'general', 'enabled') == 'yes':
            jobs.queue_job(morejobs.toggle_apate, ("no", False), unique=True)
            # context.update({'message': True})

    context.update({
        'phase': phase  # init, failed, success
    })
    return render(request, "setup.html", context)


def _setup_redis(phase):
    redis = redisDB.StrictRedis(host=settings.REDIS["HOST"], port=settings.REDIS["PORT"], db=settings.REDIS["DB"])
    redis.set(settings.SETUP_DELIMITER.join((settings.SETUP_PREFIX, settings.SETUP_KEY)), time.time())
    redis.set(settings.SETUP_DELIMITER.join((settings.SETUP_PREFIX, settings.SETUP_KEY, settings.SETUP_RES)), phase)
