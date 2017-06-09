from django.contrib.auth.decorators import login_required
from lib import jobs
import lib.utils as utils
from django.http import HttpResponse
import json
from datetime import datetime, time
from django.template.defaultfilters import date as _localdate
import time
import logging
from django.shortcuts import render

# Get an instance of a logger
logger = logging.getLogger(__name__)

@login_required
def get_devices(request):
    return render(request, "devices.html", {'messagestore': jobs.get_messages()})
