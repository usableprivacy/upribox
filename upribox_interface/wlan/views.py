# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import render
from lib import jobs, utils
from lib.info import ModelInfo
from wlan import jobs as wlanjobs

from .forms import WlanForm

# Get an instance of a logger
logger = logging.getLogger('uprilogger')


@login_required
def silent(request):
    context = {}

    if request.method == 'POST':

        form = WlanForm(utils.get_fact('wlan', 'upri', 'ssid'), request.POST)
        if form.is_valid():
            password = form.cleaned_data['password2']
            ssid = form.cleaned_data['ssid']
            jobs.queue_job(wlanjobs.reconfigure_wlan, (ssid, password))
            context.update({'message': True, 'upri_ssid': ssid})
        else:
            logger.error("form validation failed for %s" % request.path)

    else:
        form = WlanForm(utils.get_fact('wlan', 'upri', 'ssid'))

    context.update({'form': form, 'messagestore': jobs.get_messages()})
    return render(request, "silent.html", context)


@login_required
def silent_toggle(request):
    if request.method != 'POST':
        raise Http404()

    state = request.POST['enabled']
    jobs.queue_job(wlanjobs.toggle_silent, (state, ))

    return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_config')})
