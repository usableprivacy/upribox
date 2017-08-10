# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from threading import Lock

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.translation import ugettext
from lib import jobs

job_lock = Lock()


@login_required
def faq(request):
    return render(request, "faq.html", {"request": request, 'messagestore': jobs.get_messages()})


@login_required
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
            newmessages.extend(jobs.get_failed_messages())

            for i in range(len(newmessages)):
                newmessages[i]['message'] = ugettext(newmessages[i]['message'])

        finally:
            job_lock.release()

        return JsonResponse({'status': status, 'message': newmessages})

    else:
        return HttpResponse(status=503)


@login_required
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


@login_required
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


@login_required
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


@login_required
def jobstatus_failed(request):
    # if request.method != 'POST':
    #     raise Http404()

    if job_lock.acquire(False):
        try:
            # set to "done" if queue is empty (enables "close" button for modal dialog on client-side)
            # set to "processing" otherwise
            status = "failed" if jobs.check_jobs_failed() else "ok"

            # add your new messages here
            newmessages = jobs.get_failed_messages()

            for i in range(len(newmessages)):
                newmessages[i]['message'] = ugettext(newmessages[i]['message'])

        finally:
            job_lock.release()

        return JsonResponse({'status': status, 'message': newmessages})

    else:
        return HttpResponse(status=503)
