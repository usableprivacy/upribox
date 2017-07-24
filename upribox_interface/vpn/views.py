# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import Http404
from django.core.urlresolvers import reverse
from lib import jobs
from . import jobs as vpnjobs
from .models import VpnProfile
from .forms import VpnProfileForm
from django.http import JsonResponse, HttpResponse
import logging
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import time
from os.path import exists
import lib.utils as utils
from django.utils.translation import ugettext as _
import requests

logger = logging.getLogger('uprilogger')


@login_required
def check_connection(request):
    if request.method != 'POST':
        raise Http404()

    # Check VPN connectivity
    # Get log lines with TLS-auth error before connection
    try:
        with open(settings.OPENVPN_LOGFILE) as f:
            log_lines_before = f.readlines()
    except IOError:
        return HttpResponse('{{"status": "error", "msg": "{}"}}'.format(_("openvpn.log konnte nicht geöffnet werden.")))

    # Send request to upribox API
    try:
        r = requests.get("https://api.upribox.org/connectivity/", timeout=7, verify=settings.SSL_PINNING_PATH)
    except:
        return HttpResponse('{{"status": "error", "msg": "{}"}}'.format(_("Verbindung zu api.upribox.org fehlgeschlagen.")))

    # Get log lines with TLS-auth error after connection
    try:
        with open(settings.OPENVPN_LOGFILE) as f:
            log_lines_after = f.readlines()
    except IOError:
        return HttpResponse('{{"status": "error", "msg": "{}"}}'.format(_("openvpn.log konnte nicht geöffnet werden.")))

    # Count error messages in logs
    count_errors_before = 0
    for ll in log_lines_before:
        if ll.find("TLS Error") and ll.find(r.text):
            count_errors_before += 1

    count_errors_after = 0
    for ll in log_lines_after:
        if ll.find("TLS Error") and ll.find(r.text):
            count_errors_after += 1

    # Check if error messages occurred
    if count_errors_before < count_errors_after:
        # Connection succeeded
        return HttpResponse('{{"status": "success", "msg": "{}"}}'.format(_("Die Verbindung war erfolgreich!")))
    else:
        # Connection failed
        return HttpResponse('{{"status": "failure", "msg": "{}"}}'.format(_("Die Verbindung war nicht erfolgreich!")))


@login_required
def vpn_config(request):
    context = {
        'messagestore': jobs.get_messages(),
        'profiles': VpnProfile.objects.all(),
        'form': VpnProfileForm()
        }
    return render(request, "vpn.html", context)

@login_required
def vpn_get(request, slug):
    try:
        profile=VpnProfile.objects.get(slug=slug)

        # render profile
        return render(request, "vpn_profile.html", {'profile': profile})
    except VpnProfile.DoesNotExist:
        raise Http404()

@login_required
def vpn_generate(request):
    context={}

    form=VpnProfileForm(request.POST)

    if form.is_valid():
        profilename=form.cleaned_data.get('profilename')
        dyndomain=form.cleaned_data.get('dyndomain')

        logger.info("generating profile %s" % profilename)
        profile=VpnProfile(profilename=profilename, dyndomain=dyndomain)
        profile.config="# upri.box OVPN config for %s\nfoo bar baz bar OpenVPN config goes here" % profilename
        profile.save()
        if not (settings.IGNORE_MISSING_UPRICONFIG and not exists('/usr/local/bin/upri-config.py')):
            jobs.queue_job(vpnjobs.generate_profile, (str(profile.id),))
            context.update({'message': True})
        else:
            context.update({'message': False})

        context.update({'form': VpnProfileForm()})

    else:
        context.update({'form': VpnProfileForm(request.POST)})

    context.update({
            'messagestore': jobs.get_messages(),
            'profiles': VpnProfile.objects.all()})

    return render(request, "vpn.html", context)

@login_required
def vpn_delete(request, slug):
    logger.info("deleting vpn profile %s..." % slug)
    try:
        profile=VpnProfile.objects.get(slug=slug)
        profile.delete()

        try:
            logger.debug("deleting vpn profile")
            utils.exec_upri_config('delete_profile', slug)
        except utils.AnsibleError as e:
            logger.error("ansible failed with error %d: %s" % (e.rc, e.message))

        response={'deleted': 'true'}
    except VpnProfile.DoesNotExist:
        response={'deleted': 'true'}

    return JsonResponse(response)

# no login for download method required so users can easily download the config on other devices
def vpn_download(request, download_slug):
    logger.info("downloading vpn profile link %s..." % download_slug)
    try:
        # get profile by download link
        profile=VpnProfile.objects.get(download_slug=download_slug)

        # check if download link still valid
        if profile.download_valid_until is not None and profile.download_valid_until >= timezone.now():
            response=HttpResponse(profile.config, content_type='application/x-openvpn-profile')
            response['Content-Disposition']='attachment; filename="upribox-%s.ovpn"' % profile.profilename
            return response
        else:
            # link timed out
            raise Http404()
    except VpnProfile.DoesNotExist:
        # no profile found for slug => does not exist or link timed out
        raise Http404()

@login_required
def vpn_create_download(request, slug):
    try:

        # create new link and set timeout date
        profile=VpnProfile.objects.get(slug=slug)
        profile.download_valid_until=timezone.now() + timedelta(seconds=settings.VPN_LINK_TIMEOUT)
        profile.save()

        logger.info("created download link %s (valid until %s) for vpn profile %s..." % (profile.download_slug, profile.download_valid_until, slug))
        # render profile
        return render(request, "vpn_profile.html", {'profile': profile})
    except VpnProfile.DoesNotExist:
        raise Http404()

@login_required
def vpn_toggle(request):
    if request.method != 'POST':
        raise Http404()

    state=request.POST['enabled']
    jobs.queue_job(vpnjobs.toggle_vpn, (state,))

    return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_config')})
