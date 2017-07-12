import logging
from rq import Queue
from rq.job import Job
from collections import deque
from rq import get_current_job
from django.conf import settings
import django_rq
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


def job_message(message):
    job = get_current_job(connection=django_rq.get_connection())
    if not job.meta.get('messages'):
        job.meta['messages'] = deque()
    job.meta['messages'].append(message)
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
