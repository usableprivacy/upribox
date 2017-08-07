from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.http import Http404, HttpResponse
from django.utils.translation import ugettext_lazy, ugettext
from threading import Lock
from lib import jobs

job_lock = Lock()


@login_required
def faq(request):
    return render(request, "faq.html", {
        "request": request,
        'messagestore': jobs.get_messages()
    })


@login_required
def jobstatus(request):
    if request.method != 'POST':
        raise Http404()

    if job_lock.acquire(False):
        try:
            # set to "done" if queue is empty (enables "close" button for modal dialog on client-side)
            # set to "processing" otherwise
            status = "done" if jobs.check_jobs_finished() else "processing"

            # add your new messages here
            newmessages = jobs.get_messages()

            for i in range(len(newmessages)):
                newmessages[i] = ugettext(newmessages[i])

        finally:
            job_lock.release()

        return JsonResponse({'status': status, 'message': newmessages})

    else:
        return HttpResponse(status=503)


@login_required
def clear_jobstatus(request):
    if request.method != 'POST':
        raise Http404()

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
def counter_jobstatus(request):
    return render(request, "counterDummy.js")
