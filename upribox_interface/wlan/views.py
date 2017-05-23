# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .forms import WlanForm
import logging
from django.http import Http404
from lib import jobs
from wlan import jobs as wlanjobs
from django.core.urlresolvers import reverse
from lib import utils
from lib.info import ModelInfo

# Get an instance of a logger
logger = logging.getLogger('uprilogger')


@login_required
def ninja(request):
    context = {}

    if request.method == 'POST':

        form = WlanForm(utils.get_fact('wlan', 'ninja', 'ssid'), request.POST)

        if form.is_valid():
            password = form.cleaned_data['password2']
            ssid = form.cleaned_data['ssid']
            jobs.queue_job(wlanjobs.reconfigure_tor, (ssid, password))
            context.update({'message': True, 'ninja_ssid': ssid})
        else:
            logger.error("tor form validation failed for %s" % request.path)

    else:
        form = WlanForm(utils.get_fact('wlan', 'ninja', 'ssid'))

    model_info = ModelInfo()
    pi3 = model_info.runs_on_pi3()

    context.update({
        'form': form,
        'messagestore': jobs.get_messages(),
        'pi3': pi3})

    return render(request, "ninja.html", context)


@login_required
def ninja_toggle(request):
    if request.method != 'POST':
        raise Http404()

    state = request.POST['enabled']
    jobs.queue_job(wlanjobs.toogle_tor, (state,))

    return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_ninja')})


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
    jobs.queue_job(wlanjobs.toggle_silent, (state,))

    return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_silent')})
