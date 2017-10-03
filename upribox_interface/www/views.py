# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from threading import Lock

from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext
from django.views.decorators.http import (require_GET, require_http_methods,
                                          require_POST)
from lib import jobs, utils

job_lock = Lock()


@require_GET
@login_required
def faq(request):
    return render(request, "faq.html", {"request": request, 'messagestore': jobs.get_messages()})


@require_POST
@user_passes_test(utils.check_authorization)
def jobstatus(request):
    # if request.method != 'POST':
    #     raise Http404()

    if job_lock.acquire(False):
        try:
            # set to "done" if queue is empty (enables "close" button for modal dialog on client-side)
            # set to "processing" otherwise
            status = "done" if jobs.check_jobs_finished() else "processing"
            if jobs.check_jobs_failed():
                status = "failed"

            # add your new messages here
            newmessages = jobs.get_messages()
            newmessages.extend([entry for entry in jobs.get_failed_messages() if entry['status'] == "error"])

            for i in range(len(newmessages)):
                newmessages[i]['message'] = ugettext(newmessages[i]['message'])

        finally:
            job_lock.release()

        return JsonResponse({'status': status, 'message': newmessages})

    else:
        return HttpResponse(status=503)


@require_POST
@user_passes_test(utils.check_authorization)
def clear_jobstatus(request):
    # if request.method != 'POST':
    #     raise Http404()

    if job_lock.acquire(False):
        try:
            if jobs.check_jobs_finished():
                jobs.clear_jobs()

        finally:
            job_lock.release()

        return JsonResponse({'status': 'ok'})

    else:
        return HttpResponse(status=503)


@require_POST
@user_passes_test(utils.check_authorization)
def jobcounter(request):
    # if request.method != 'POST':
    #     raise Http404()

    if job_lock.acquire(False):
        count = 0
        errors = 0
        try:
            if jobs.check_jobs_finished():
                jobs.clear_jobs()
            count = len(jobs.get_messages())

            errors = len(jobs.get_failed_messages())

        finally:
            job_lock.release()

        response = {'count': count}

        if errors:
            response.update({'errorcount': errors})

        return JsonResponse(response)

    else:
        return HttpResponse(status=503)


@require_POST
@user_passes_test(utils.check_authorization)
def clear_failed(request):
    # if request.method != 'POST':
    #     raise Http404()

    if job_lock.acquire(False):
        try:
            if jobs.check_jobs_failed():
                jobs.clear_failed()

        finally:
            job_lock.release()

        return JsonResponse({'status': 'ok'})

    else:
        return HttpResponse(status=503)


@require_POST
@user_passes_test(utils.check_authorization)
def jobstatus_failed(request):
    # if request.method != 'POST':
    #     raise Http404()

    if job_lock.acquire(False):
        try:
            # set to "done" if queue is empty (enables "close" button for modal dialog on client-side)
            # set to "processing" otherwise
            status = "failed" if jobs.check_jobs_failed() else "ok"

            # add your new messages here
            newmessages = [entry for entry in jobs.get_failed_messages() if entry['status'] == "error"]

            for i in range(len(newmessages)):
                newmessages[i]['message'] = ugettext(newmessages[i]['message'])

        finally:
            job_lock.release()

        return JsonResponse({'status': status, 'message': newmessages})

    else:
        return HttpResponse(status=503)
