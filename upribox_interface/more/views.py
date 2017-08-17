# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from datetime import datetime

import redis as redisDB
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from lib import jobs, utils
from lib.info import UpdateStatus
from wlan import jobs as wlanjobs

from . import jobs as sshjobs
from .forms import AdminForm, StaticIPForm

# Get an instance of a logger
logger = logging.getLogger('uprilogger')


@require_http_methods(["GET", "POST"])
@login_required
def more_overview(request):
    context = {}
    redis = redisDB.StrictRedis(host=settings.REDIS["HOST"], port=settings.REDIS["PORT"], db=settings.REDIS["DB"])

    context.update({'setup_result': redis.get(settings.SETUP_DELIMITER.join((settings.SETUP_PREFIX, settings.SETUP_KEY, settings.SETUP_RES)))})
    try:
        timestamp = float(redis.get(settings.SETUP_DELIMITER.join((settings.SETUP_PREFIX, settings.SETUP_KEY))))
        setup_date = datetime.utcfromtimestamp(timestamp)
    except (TypeError, ValueError):
        context.update({'setup_date': None})
    else:
        context.update({'setup_date': setup_date})
    return render(request, "config.html", context)


@require_http_methods(["GET", "POST"])
@login_required
def more_user(request):
    context = {}

    form = AdminForm(request)
    if request.method == 'POST':

        form = AdminForm(request, request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['password2']
            new_username = form.cleaned_data['username']

            old_password = form.cleaned_data['oldpassword']
            old_username = request.user.username

            logger.info("updating user %s..." % old_username)
            u = User.objects.get(username=old_username)

            # sanity check, this should never happen
            if not u:
                logger.error("unexpected error: user %s does not exist" % old_username)
                return HttpResponse(status=500)

            u.set_password(new_password)
            u.username = new_username
            u.save()
            logger.info("user %s updated to %s (password changed: %s)" % (old_username, new_username, new_password != old_password))
            context.update({'message': True})

        else:
            logger.error("admin form validation failed")

    context.update({
        'form': form,
        'messagestore': jobs.get_messages(),
    })

    return render(request, "user.html", context)


@require_http_methods(["GET", "POST"])
@login_required
def more_static(request, enable=None, dhcpd=None):
    context = {}

    net_info = utils.get_system_network_config()
    ip_form = StaticIPForm(
        net_info['ip'],
        net_info['netmask'],
        net_info['gateway'],
        net_info['dns_servers'][0],
        utils.get_fact('dhcpd', 'general', 'enabled'),
    )

    if request.method == 'POST':

        ip_form = StaticIPForm(
            net_info['ip'], net_info['netmask'], net_info['gateway'], net_info['dns_servers'][0],
            utils.get_fact('dhcpd', 'general', 'enabled'), request.POST
        )
        if ip_form.is_valid():
            ip = ip_form.cleaned_data['ip_address']
            netmask = ip_form.cleaned_data['ip_netmask']
            gateway = ip_form.cleaned_data['gateway']
            dns = ip_form.cleaned_data['dns_server']
            # dhcp = ip_form.cleaned_data['dhcp_server']

            jobs.queue_job(sshjobs.reconfigure_network, (ip, netmask, gateway, dns, enable))
            jobs.queue_job(sshjobs.toggle_dhcpd, ("yes" if dhcpd else "no", ))

            context.update({
                'message': True,
                "refresh_url": request.path,  # reverse('upri_config_static'),
                'messagestore': jobs.get_messages()
            })

    context.update({
        'ip_form': ip_form,
        'messagestore': jobs.get_messages(),
        'href': request.path,
    })

    return render(request, "static.html", context)


@login_required
def ssh_toggle(request):
    if request.method != 'POST':
        raise Http404()

    state = request.POST['enabled']
    jobs.queue_job(sshjobs.toggle_ssh, (state, ))

    return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_config')})


@login_required
def apate_toggle(request):
    if request.method != 'POST':
        raise Http404()

    state = request.POST['enabled']
    jobs.queue_job(sshjobs.toggle_dhcpd, ('no', ))
    jobs.queue_job(sshjobs.toggle_apate, (state, ))

    return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_config')})


@login_required
def static_toggle(request):
    if request.method != 'POST':
        raise Http404()

    current = [
        utils.get_fact('interfaces', 'static', 'ip', defaults=False),
        utils.get_fact('interfaces', 'static', 'netmask', defaults=False),
        utils.get_fact('interfaces', 'static', 'dns', defaults=False),
        utils.get_fact('interfaces', 'static', 'gateway', defaults=False),
    ]

    state = request.POST.get('enabled', None)
    if all(current) or state == 'no':
        # all requirements met or dhcp requested
        jobs.queue_job(sshjobs.toggle_static, (state, ))
        return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_config')})
    else:
        # not all requirements met
        return HttpResponseForbidden(reverse('upri_config_static_enable'))


@login_required
def manual_toggle(request):
    if request.method != 'POST':
        raise Http404()

    current = [
        utils.get_fact('interfaces', 'static', 'ip', defaults=False),
        utils.get_fact('interfaces', 'static', 'netmask', defaults=False),
        utils.get_fact('interfaces', 'static', 'dns', defaults=False),
        utils.get_fact('interfaces', 'static', 'gateway', defaults=False),
    ]

    if all(current):
        # all requirements met or dhcp requested
        jobs.queue_job(sshjobs.toggle_apate, ('no', ))
        jobs.queue_job(sshjobs.toggle_static, ('yes', ))
        jobs.queue_job(sshjobs.toggle_dhcpd, ('yes', ))
        return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_config')})
    else:
        # not all requirements met
        return HttpResponseForbidden(reverse('upri_config_static_dhcpd'))


@login_required
def wifi_mode(request):
    if request.method != 'POST':
        raise Http404()

    jobs.queue_job(wlanjobs.toggle_silent, ('yes', ))
    jobs.queue_job(sshjobs.toggle_apate, ('no', ))
    jobs.queue_job(sshjobs.toggle_dhcpd, ('no', ))
    return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_config')})


@require_http_methods(["GET", "POST"])
@login_required
def show_modal(request):
    return render(request, "modal.html")
