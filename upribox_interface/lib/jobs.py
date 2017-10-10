import logging
from collections import deque

import django_rq
from django.conf import settings
from rq import Queue, get_current_job
from rq.job import Job
from rq.registry import FinishedJobRegistry, StartedJobRegistry

logger = logging.getLogger('uprilogger')

q = django_rq.get_queue()
# rqq = Queue(connection=django_rq.get_connection())
finished_job_registry = FinishedJobRegistry(connection=django_rq.get_connection())
started_job_registry = StartedJobRegistry(connection=django_rq.get_connection())
failed_queue = django_rq.get_failed_queue()

#
# Job management
#


def job_message(message, status="success"):
    job = get_current_job(connection=django_rq.get_connection())
    if not job.meta.get('messages'):
        job.meta['messages'] = deque()
    job.meta['messages'].append({"message": message, "status": status})
    job.save_meta()
    job.save()


def job_error(message):
    job_message(message, status="error")


def job_clear_messages():
    job = get_current_job(connection=django_rq.get_connection())
    job.meta['messages'] = deque()
    job.save_meta()
    job.save()


def queue_job(job, args, unique=False):
    # set job description to function name in order to avoid logging parameters
    if not unique or not job.__name__ in [entry.description for entry in q.jobs]:
        q.enqueue(job, *args, description=job.__name__)


def clear_jobs():
    # deletes all "old" finished jobs
    finished_job_registry.cleanup(timestamp="+inf")


def check_jobs_finished():
    return True if q.is_empty() and not started_job_registry.get_job_ids() else False


def check_jobs_failed():
    return not failed_queue.is_empty()


def get_messages():
    msg = []
    for job in finished_job_registry.get_job_ids():
        fetched = q.fetch_job(job)
        if fetched:
            cur_msgs = fetched.meta.get('messages')
            if cur_msgs:
                try:
                    while True:
                        msg.append(cur_msgs.popleft())
                except IndexError:
                    pass

    for job in q.get_job_ids():
        fetched = q.fetch_job(job)
        if fetched:
            cur_msgs = fetched.meta.get('messages')
            if cur_msgs:
                try:
                    while True:
                        msg.append(cur_msgs.popleft())
                except IndexError:
                    pass

    for job in started_job_registry.get_job_ids():
        fetched = q.fetch_job(job)
        if fetched:
            cur_msgs = fetched.meta.get('messages')
            if cur_msgs:
                try:
                    while True:
                        msg.append(cur_msgs.popleft())
                except IndexError:
                    pass

    return msg


def get_failed_messages():
    msg = []

    for job in failed_queue.get_job_ids():
        fetched = q.fetch_job(job)
        if fetched:
            cur_msgs = fetched.meta.get('messages')
            if cur_msgs:
                try:
                    while True:
                        msg.append(cur_msgs.popleft())
                except IndexError:
                    pass

    return msg


def clear_failed():
    # deletes all "old" finished jobs
    failed_queue.empty()


class JobFailedError(Exception):
    pass
