# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from lib import jobs, info
import redis as redisDB
from django.conf import settings
from more import jobs as morejobs
# from . import jobs as morejobs

logger = logging.getLogger('uprilogger')


@login_required
@require_http_methods(["GET", "POST"])
def setup(request, phase):
    context = {}

    if phase in ["success", "error"]:
        redis = redisDB.StrictRedis(host=settings.REDIS["HOST"], port=settings.REDIS["PORT"], db=settings.REDIS["DB"])
        redis.set(settings.SETUP_DELIMITER.join((settings.SETUP_PREFIX, settings.SETUP_KEY)), str(True))
        if phase == "error" and not info.check_ipv6():
            jobs.queue_job(morejobs.toggle_apate, ("no",))
            context.update({'message': True})
    elif phase == "init" and not info.check_ipv6():
        jobs.queue_job(morejobs.toggle_apate, ("yes",))
        context.update({'message': True})

    if phase == "init" and info.check_ipv6():
        return redirect('upri_setup_error')
    else:
        context.update({
            'messagestore': jobs.get_messages(),
            'phase': phase  # init, error, success
        })
        return render(request, "setup.html", context)
