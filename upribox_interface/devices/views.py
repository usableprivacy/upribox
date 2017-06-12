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

# Get an instance of a logger
logger = logging.getLogger('uprilogger')


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
        device = DeviceEntry.objects.get(id=request.POST.get('dev_id', None))
    except DeviceEntry.DoesNotExist:
        device = None
    jobs.queue_job(devicejobs.toggle_device_mode, (mode, device))

    return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_devices')})
