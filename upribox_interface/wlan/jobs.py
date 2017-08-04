# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

import lib.jobs as jobs
import lib.utils as utils
from django.utils.translation import ugettext as _

logger = logging.getLogger('uprilogger')


def reconfigure_wlan(ssid, password):
    try:
        jobs.job_message(_("Das Silent WLAN wird neu konfiguriert..."))
        try:
            if ssid:
                logger.debug("new ssid: %s" % ssid)
                jobs.job_message(_("Name wird geändert..."))
                utils.exec_upri_config('set_ssid', ssid)
            if password:
                logger.debug("new password: %s" % password)
                jobs.job_message(_("Passwort wird geändert..."))
                utils.exec_upri_config('set_password', password)
            if password or ssid:
                jobs.job_message(_("Wlan wird neu gestartet..."))
                logger.debug("restarting wlan")
                utils.exec_upri_config('restart_wlan')

            jobs.job_message(_("Konfiguration des WLANs erfolgreich."))

        except utils.AnsibleError as e:
            logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
            # jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten. Fehlercode: %(errorcode)s" % {'errorcode': e.rc}))
            raise

    except Exception as e:
        logger.exception(e)
        jobs.job_clear_messages()
        jobs.job_message(_("Konfiguration des WLANs fehlgeschlagen."))
        raise jobs.JobFailedError()


def toggle_silent(state):
    try:
        if state in ['yes', 'no']:
            try:
                if state == 'yes':
                    jobs.job_message(_("silent WLAN wird gestartet..."))
                else:
                    jobs.job_message(_("silent WLAN wird gestoppt..."))

                logger.debug("restarting silent")
                utils.exec_upri_config('enable_silent', state)
                if state == 'no':
                    utils.exec_upri_config('enable_tor', 'no')
                    utils.exec_upri_config('restart_tor')
                else:
                    utils.exec_upri_config('restart_silent')
                jobs.job_message(_("Konfiguration des silent WLAN erfolgreich."))

            except utils.AnsibleError as e:
                logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
                raise
        else:
            jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten."))
            raise jobs.JobFailedError()

    except Exception as e:
        logger.exception(e)
        jobs.job_clear_messages()
        jobs.job_message(_("Konfiguration des WLANs fehlgeschlagen."))
        raise jobs.JobFailedError()
