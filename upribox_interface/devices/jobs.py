# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
import sqlite3

import lib.jobs as jobs
import lib.utils as utils
from django.utils.translation import ugettext as _

from .models import DeviceEntry

logger = logging.getLogger('uprilogger')


def toggle_device_mode(mode, device):
    dbfile = None
    try:
        if mode in [entry[0] for entry in DeviceEntry.MODES]:
            if device:
                try:
                    with open('/etc/ansible/default_settings.json', 'r') as f:
                        config = json.load(f)
                except IOError as e:
                    logger.error('Cannot read Default Settings File: ' + e.strerror)
                    raise

                dbfile = config['django']['db']

                jobs.job_message(_("Gerätemodus wird geändert..."))

                try:
                    if mode == "SL":
                        utils.exec_upri_config('silent_device', device.mac)
                    elif mode == "NJ":
                        utils.exec_upri_config('torify_device', device.mac)
                    elif mode == "NO":
                        utils.exec_upri_config('exclude_device', device.mac)

                    logger.debug("configuring device modes")
                    utils.exec_upri_config('configure_devices')

                except utils.AnsibleError as e:
                    logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
                    raise

                try:
                    with sqlite3.connect(dbfile) as conn:
                        c = conn.cursor()
                        c.execute("Update devices_deviceentry set mode=?, changing=? where id=?;", (mode, False, device.id))
                        conn.commit()
                except sqlite3.Error as dbe:
                    # logger.exception(dbe)
                    raise

                jobs.job_message(_("Gerätemodus erfolgreich geändert."))

            else:
                logger.error("device id unknown")
                raise jobs.JobFailedError()
        else:
            logger.error("something unexpected happened")
            # jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten."))
            raise jobs.JobFailedError()
    except Exception as e:
        logger.exception(e)
        # jobs.job_clear_messages()
        jobs.job_error(_("Ändern des Gerätemodus fehlgeschlagen."))
        try:
            with sqlite3.connect(dbfile) as conn:
                c = conn.cursor()
                c.execute("Update devices_deviceentry set changing=? where id=?;", (False, device.id))
                conn.commit()
        except Exception:
            # logger.exception(dbe)
            raise jobs.JobFailedError()
        raise jobs.JobFailedError()

def fail_dummy(test):
    # jobs.job_clear_messages()
    jobs.job_error(_("Job fehlgeschlagen."))
    raise jobs.JobFailedError()
