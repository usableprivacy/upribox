# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from lib import jobs
from .forms import AdminForm
import logging
from django.contrib.auth.models import User
from . import jobs as sshjobs
from django.core.urlresolvers import reverse

# Get an instance of a logger
logger = logging.getLogger('uprilogger')

@login_required
def more_config(request):
    context = RequestContext(request)

    if request.method == 'POST':

        form = AdminForm(request, request.POST)

        if form.is_valid():
            new_password = form.cleaned_data['password2']
            new_username = form.cleaned_data['username']

            old_password = form.cleaned_data['oldpassword']
            old_username = request.user.username

            logger.info("updating user %s..." % old_username)
            u = User.objects.get(username=old_username)

            #sanity check, this should never happen
            if not u:
                logger.error("unexpected error: user %s does not exist" % old_username)
                return HttpResponse(status=500)

            u.set_password(new_password)
            u.username = new_username
            u.save()
            logger.info("user %s updated to %s (password changed: %s)" % (old_username, new_username, new_password != old_password) )
            context.push({'message': True})

        else:
            logger.error("admin form validation failed")

    else:
        form = AdminForm(request)

    context.push({
        'form': form,
        'messagestore': jobs.get_messages()})

    return render_to_response("more.html", context)

@login_required
def ssh_toggle(request):
    if request.method != 'POST':
        raise Http404()

    state = request.POST['enabled']
    jobs.queue_job(sshjobs.toggle_ssh, (state,))

    return render_to_response("modal.html", {"message": True, "refresh_url": reverse('upri_more')})

@login_required
def apate_toggle(request):
    if request.method != 'POST':
        raise Http404()

    state = request.POST['enabled']
    jobs.queue_job(sshjobs.toggle_apate, (state,))

    return render_to_response("modal.html", {"message": True, "refresh_url": reverse('upri_more')})
