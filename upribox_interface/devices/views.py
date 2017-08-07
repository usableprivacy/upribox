# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from lib import jobs
import lib.utils as utils
from django.http import HttpResponse
import json
from datetime import datetime, time
from django.template.defaultfilters import date as _localdate
import time
import logging
from django.shortcuts import render
from .models import DeviceEntry
from django.core.urlresolvers import reverse
from . import jobs as devicejobs
from django.views.decorators.http import require_http_methods
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from django.template import loader
from django.http import JsonResponse


# Get an instance of a logger
logger = logging.getLogger('uprilogger')


@require_http_methods(["GET", "POST"])
@login_required
def get_devices(request):
    try:
        utils.exec_upri_config('parse_user_agents')
    except utils.AnsibleError as ae:
        logger.exception(ae)

    return render(request, "devices.html", {'messagestore': jobs.get_messages(), 'devices':  DeviceEntry.objects.all(), })


@login_required
@require_POST
def set_device_mode(request):
    mode = request.POST.get('mode', None)
    try:
        device = DeviceEntry.objects.get(slug=request.POST.get('dev_id', None))
    except DeviceEntry.DoesNotExist:
        device = None
    jobs.queue_job(devicejobs.toggle_device_mode, (mode, device))

    return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_devices')})


@login_required
@require_http_methods(["GET", "POST"])
def change_name(request, slug):
    if request.method == 'POST':
        name_mode = request.POST.get("changeName", None)
        suggestion = request.POST.get("suggestion", None)
        chosen_name = request.POST.get("chosenName", None)

        if not name_mode or name_mode not in ("suggestion", "chosenName"):
            raise Http404("invalid request")

        if name_mode == "suggestion":
            if not suggestion:
                raise Http404("invalid request")
            else:
                dev = DeviceEntry.objects.get(slug=slug)
                dev.chosen_name = suggestion
                dev.save()
        elif name_mode == "chosenName":
            if not chosen_name:
                temp = loader.get_template('name_modal.html')
                message = {
                    "device": DeviceEntry.objects.get(slug=slug),
                    "href": reverse('upri_device_name', kwargs={'slug': slug}),
                    "error": _("Der gewählte Name darf nicht leer sein")
                }
                return HttpResponse(temp.render(message, request), content_type='text/html; charset=utf-8', status=404)
            else:
                dev = DeviceEntry.objects.get(slug=slug)
                dev.chosen_name = chosen_name
                dev.save()

        return render(request, "devices.html", {'messagestore': jobs.get_messages(), 'devices':  DeviceEntry.objects.all(), })
    else:
        return render(request, "name_modal.html", {"device": DeviceEntry.objects.get(slug=slug), "href": reverse('upri_device_name', kwargs={'slug': slug})})


@login_required
@require_http_methods(["GET", "POST"])
def get_device_status(request, slug):
    try:
        ip = DeviceEntry.objects.get(slug=slug).ip
    except DeviceEntry.DoesNotExist:
        res = None
    else:
        res = utils.exec_upri_config("check_device", ip)

    return JsonResponse({slug: bool(res)})

@login_required
def single_device_template(request):
    return render(request, "device_entry.html")

@login_required
def complete_device_list(request):
    return render (request, "deviceListDummy.js")

@login_required
def in_progress_devices (request):
    return render (request, "deviceProgressListDummy.js")

@login_required
def get_online_state (request):
    return get_online_state_with_slug(request, -1)

@login_required
def get_online_state_with_slug (request, slug):
    return render (request, "devicesOnlineReq.js")