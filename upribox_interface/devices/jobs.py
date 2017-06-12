# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import lib.jobs as jobs
import lib.utils as utils
from django.utils.translation import ugettext as _
import logging
from .models import DeviceEntry
logger = logging.getLogger('uprilogger')
from django.conf import settings
from django.db import DatabaseError
import sqlite3
import json

def toggle_device_mode(mode, device):

    if mode in [entry[0] for entry in DeviceEntry.MODES]:
        if device:
            try:
                jobs.job_message(_("Gerätemodus wird geändert..."))
                if mode == "SL":
                    utils.exec_upri_config('silent_device', device.mac)
                elif mode == "NJ":
                    utils.exec_upri_config('torify_device', device.mac)
                elif mode == "NO":
                    utils.exec_upri_config('exclude_device', device.mac)

                logger.debug("configuring device modes")

                utils.exec_upri_config('configure_devices')


                try:
                    with open('/etc/ansible/default_settings.json', 'r') as f:
                        config = json.load(f)
                except IOError as e:
                    logger.error('Cannot read Default Settings File: ' + e.strerror)
                    raise utils.AnsibleError("Cannot read Default Settings File", 2)

                dbfile = config['django']['db']
                try:
                    conn = sqlite3.connect(dbfile)
                    # conn = sqlite3.connect(settings.DATABASES['default']['NAME'])
                    c = conn.cursor()
                    c.execute("Update devices_deviceentry set mode=? where id=?;", (mode, device.id))
                    conn.commit()
                    conn.close()
                except DatabaseError as dbe:
                    logger.exception(dbe)
                    raise utils.AnsibleError("failed to write to database", 2)

                jobs.job_message(_("Gerätemodus erfolgreich geändert."))
            except utils.AnsibleError as e:
                logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
                jobs.job_message(_("Ändern des Gerätemodus fehlgeschlagen."))
        else:
            logger.error("device id unknown")
            jobs.job_message(_("Ändern des Gerätemodus fehlgeschlagen."))
    else:
        jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten."))
