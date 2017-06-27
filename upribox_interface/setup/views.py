# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from lib import jobs
import logging

logger = logging.getLogger('uprilogger')


@login_required
@require_http_methods(["GET", "POST"])
def setup(request, phase):
    context = {}

    context.update({
        'messagestore': jobs.get_messages(),
        'phase': phase
    })

    return render(request, "setup.html", context)
