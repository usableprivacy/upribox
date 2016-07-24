# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import lib.jobs as jobs
import lib.utils as utils
from django.utils.translation import ugettext as _
import logging
logger = logging.getLogger('uprilogger')


def toggle_ssh(state):

    if state in ['yes', 'no']:
        try:
            if state == 'yes':
                jobs.job_message(_("SSH wird gestartet..."))
            else:
                jobs.job_message(_("SSH wird gestoppt..."))

            logger.debug("restarting ssh")
            utils.exec_upri_config('enable_ssh', state)
            utils.exec_upri_config('restart_ssh')
            jobs.job_message(_("Konfiguration von SSH erfolgreich."))

        except utils.AnsibleError as e:
            logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
            if state == 'yes':
                jobs.job_message(_("Starten von SSH fehlgeschlagen."))
            else:
                jobs.job_message(_("Stoppen von SSH fehlgeschlagen."))
    else:
        jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten."))

def toggle_apate(state):

    if state in ['yes', 'no']:
        try:
            if state == 'yes':
                jobs.job_message(_("Apate ARP Spoofing Daemon wird gestartet..."))
            else:
                jobs.job_message(_("Apate ARP Spoofing Daemon wird gestoppt..."))

            logger.debug("restarting apate")
            utils.exec_upri_config('enable_apate', state)
            utils.exec_upri_config('restart_apate')
            jobs.job_message(_("Konfiguration von Apate ARP Spoofing Daemon erfolgreich."))

        except utils.AnsibleError as e:
            logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
            if state == 'yes':
                jobs.job_message(_("Starten von Apate ARP Spoofing Daemon fehlgeschlagen."))
            else:
                jobs.job_message(_("Stoppen von Apate ARP Spoofing Daemon fehlgeschlagen."))
    else:
        jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten."))
