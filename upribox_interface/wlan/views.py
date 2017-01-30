# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from .forms import WlanForm
from django.template import RequestContext
import logging
from django.http import Http404
from lib import jobs
from wlan import jobs as wlanjobs
from django.core.urlresolvers import reverse
from lib import utils
from lib.info import HardwareInfo, ModelInfo
from django.http import HttpResponse

# Get an instance of a logger
logger = logging.getLogger('uprilogger')


@login_required
def ninja(request):
    context = RequestContext(request)

    if request.method == 'POST':

        form = WlanForm(utils.get_fact('wlan', 'ninja', 'ssid'), request.POST)

        if form.is_valid():
            password = form.cleaned_data['password2']
            ssid = form.cleaned_data['ssid']
            jobs.queue_job(wlanjobs.reconfigure_tor, (ssid, password))
            context.push({'message': True, 'ninja_ssid':ssid})
        else:
            logger.error("tor form validation failed for %s" % request.path)

    else:
        form = WlanForm(utils.get_fact('wlan','ninja','ssid'))

    model_info = ModelInfo()
    pi3 = model_info.runs_on_pi3()

    context.push({
        'form': form,
        'messagestore': jobs.get_messages(),
        'pi3': pi3})

    return render_to_response("ninja.html", context)


@login_required
def ninja_toggle(request):
    if request.method != 'POST':
        raise Http404()

    state = request.POST['enabled']
    jobs.queue_job(wlanjobs.toogle_tor, (state,))

    return render_to_response("modal.html", {"message": True, "refresh_url": reverse('upri_ninja')})


@login_required
def silent(request):
    context = RequestContext(request)

    if request.method == 'POST':

        form = WlanForm(utils.get_fact('wlan', 'upri', 'ssid'), request.POST)
        if form.is_valid():
            password = form.cleaned_data['password2']
            ssid = form.cleaned_data['ssid']
            jobs.queue_job(wlanjobs.reconfigure_wlan, (ssid, password))
            context.push({'message': True, 'upri_ssid': ssid})
        else:
            logger.error("form validation failed for %s" % request.path)

    else:
        form = WlanForm(utils.get_fact('wlan', 'upri', 'ssid'))

    context.push({'form': form})
    context.push({'messagestore': jobs.get_messages()})
    return render_to_response("silent.html", context)

@login_required
def silent_toggle(request):
    if request.method != 'POST':
        raise Http404()

    state = request.POST['enabled']
    jobs.queue_job(wlanjobs.toggle_silent, (state,))

    return render_to_response("modal.html", {"message": True, "refresh_url": reverse('upri_silent')})

@login_required
def check_pi3(request):
    hw = HardwareInfo()
    if hw.runs_on_pi3():
        return HttpResponse('{"pi3": "yes"}')
    else:
        return HttpResponse('{"pi3": "no"}')
