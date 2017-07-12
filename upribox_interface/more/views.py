# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import Http404, HttpResponse
from lib import jobs, utils
from lib.info import UpdateStatus
from .forms import AdminForm, StaticIPForm
import logging
from django.contrib.auth.models import User
from . import jobs as sshjobs
from django.core.urlresolvers import reverse
import redis as redisDB
from django.conf import settings
from datetime import datetime

# Get an instance of a logger
logger = logging.getLogger('uprilogger')


@login_required
def more_config(request, save_form):
    context = {}

    form = AdminForm(request)
    net_info = utils.get_system_network_config()
    ip_form = StaticIPForm(net_info['ip'], net_info['netmask'], net_info['gateway'], net_info['dns_servers'][0], utils.get_fact('dhcpd', 'general', 'enabled'))

    if request.method == 'POST':

        if save_form == "user":
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
        elif save_form == "static_ip":
            ip_form = StaticIPForm(net_info['ip'], net_info['netmask'], net_info['gateway'], net_info['dns_servers'][0],
                                   utils.get_fact('dhcpd', 'general', 'enabled'), request.POST)
            if ip_form.is_valid():
                ip = ip_form.cleaned_data['ip_address']
                netmask = ip_form.cleaned_data['ip_netmask']
                gateway = ip_form.cleaned_data['gateway']
                dns = ip_form.cleaned_data['dns_server']
                dhcp = ip_form.cleaned_data['dhcp_server']
                jobs.queue_job(sshjobs.reconfigure_network, (ip, netmask, gateway, dns, dhcp))
                context.update({
                    'message': True,
                    "refresh_url": reverse('upri_more'),
                    'messagestore': jobs.get_messages()
                })

    update_status = UpdateStatus()

    context.update({
        'form': form,
        'ip_form': ip_form,
        'messagestore': jobs.get_messages(),
        'update_time': update_status.update_utc_time,
        'version': update_status.get_version()
    })

    return render(request, "more.html", context)


@login_required
def more_overview(request):
    context = {}
    redis = redisDB.StrictRedis(host=settings.REDIS["HOST"], port=settings.REDIS["PORT"], db=settings.REDIS["DB"])

    try:
        timestamp = float(redis.get(settings.SETUP_DELIMITER.join((settings.SETUP_PREFIX, settings.SETUP_KEY))))
        setup_date = datetime.utcfromtimestamp(timestamp)
    except (TypeError, ValueError):
        context.update({
            'setup_date': None
        })
    else:
        context.update({
            'setup_date': setup_date
        })
    return render(request, "config.html", context)


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


@login_required
def more_static(request):
    context = {}

    net_info = utils.get_system_network_config()
    ip_form = StaticIPForm(net_info['ip'], net_info['netmask'], net_info['gateway'], net_info['dns_servers'][0], utils.get_fact('dhcpd', 'general', 'enabled'))

    if request.method == 'POST':

        ip_form = StaticIPForm(net_info['ip'], net_info['netmask'], net_info['gateway'], net_info['dns_servers'][0],
                               utils.get_fact('dhcpd', 'general', 'enabled'), request.POST)
        if ip_form.is_valid():
            ip = ip_form.cleaned_data['ip_address']
            netmask = ip_form.cleaned_data['ip_netmask']
            gateway = ip_form.cleaned_data['gateway']
            dns = ip_form.cleaned_data['dns_server']
            # dhcp = ip_form.cleaned_data['dhcp_server']

            # TODO fix queue job (dhcp)
            jobs.queue_job(sshjobs.reconfigure_network, (ip, netmask, gateway, dns))
            context.update({
                'message': True,
                "refresh_url": reverse('upri_config_static'),
                'messagestore': jobs.get_messages()
            })

    context.update({
        'ip_form': ip_form,
        'messagestore': jobs.get_messages(),
    })

    return render(request, "static.html", context)


@login_required
def ssh_toggle(request):
    if request.method != 'POST':
        raise Http404()

    state = request.POST['enabled']
    jobs.queue_job(sshjobs.toggle_ssh, (state,))

    return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_more')})


@login_required
def apate_toggle(request):
    if request.method != 'POST':
        raise Http404()

    state = request.POST['enabled']
    jobs.queue_job(sshjobs.toggle_apate, (state,))

    return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_more')})


@login_required
def save_static(request):
    if request.method != 'POST':
        raise Http404()

    jobs.queue_job(sshjobs.toggle_static, ('yes',))

    return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_more')})


@login_required
def save_dhcp(request):
    if request.method != 'POST':
        raise Http404()

    jobs.queue_job(sshjobs.toggle_static, ('no',))

    return render(request, "modal.html", {"message": True, "refresh_url": reverse('upri_more')})
