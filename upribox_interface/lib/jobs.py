import logging
from rq import Queue
from redis import Redis
from collections import deque
from rq import get_current_job
from django.conf import settings
import django_rq
from rq.registry import FinishedJobRegistry, StartedJobRegistry

logger = logging.getLogger('uprilogger')

q = django_rq.get_queue()
finished_job_registry = FinishedJobRegistry(connection=django_rq.get_connection())
started_job_registry = StartedJobRegistry(connection=django_rq.get_connection())
failed_queue = django_rq.get_failed_queue()


#
# Job management
#


def job_message(message):
    job = get_current_job(connection=django_rq.get_connection())
    if not job.meta.get('messages'):
        job.meta['messages'] = deque()
    job.meta['messages'].append(message)
    job.save()


def queue_job(job, args):
    q.enqueue(job, *args)


def clear_jobs():
    # deletes all "old" finished jobs
    finished_job_registry.cleanup(timestamp="+inf")


def check_jobs_finished():
    return True if q.is_empty() and not started_job_registry.get_job_ids() else False


def get_messages():
    msg = []
    for job in finished_job_registry.get_job_ids():
        cur_msgs = q.fetch_job(job).meta.get('messages')
        if cur_msgs:
            try:
                while True:
                    msg.append(cur_msgs.popleft())
            except IndexError:
                pass

    for job in q.get_job_ids():
        cur_msgs = q.fetch_job(job).meta.get('messages')
        if cur_msgs:
            try:
                while True:
                    msg.append(cur_msgs.popleft())
            except IndexError:
                pass

    for job in started_job_registry.get_job_ids():
        cur_msgs = q.fetch_job(job).meta.get('messages')
        if cur_msgs:
            try:
                while True:
                    msg.append(cur_msgs.popleft())
            except IndexError:
                pass

    return msg
