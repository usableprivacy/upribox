# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import lib.jobs as jobs
import lib.utils as utils
from django.utils.translation import ugettext as _
import logging
logger = logging.getLogger('uprilogger')


def reconfigure_wlan(ssid, password):

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

        jobs.job_message(_("Konfiguration erfolgreich"))

    except utils.AnsibleError as e:
        logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
        jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten. Fehlercode: %(errorcode)s" % {'errorcode': e.rc}))


def reconfigure_tor(ssid, password):

    jobs.job_message(_("Das Ninja WLAN wird neu konfiguriert..."))

    try:
        if ssid:
            logger.debug("new tor ssid: %s" % ssid)
            jobs.job_message(_("Name wird geändert..."))
            utils.exec_upri_config('set_tor_ssid', ssid)
        if password:
            logger.debug("new tor password")
            jobs.job_message(_("Passwort wird geändert..."))
            utils.exec_upri_config('set_tor_password', password)
        if password or ssid:
            logger.debug("restarting tor wlan")
            jobs.job_message(_("WLAN wird neu gestartet..."))
            utils.exec_upri_config('restart_wlan')

        jobs.job_message(_("Konfiguration erfolgreich."))

    except utils.AnsibleError as e:
        logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
        jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten. Fehlercode: %(errorcode)s" % {'errorcode': e.rc}))


def toggle_tor(state):

    if state in ['yes', 'no']:
        try:
            if state == 'yes':
                jobs.job_message(_("ninja WLAN wird gestartet..."))
            else:
                jobs.job_message(_("ninja WLAN wird gestoppt..."))

            logger.debug("restarting tor")
            utils.exec_upri_config('enable_tor', state)
            utils.exec_upri_config('restart_tor')
            jobs.job_message(_("Konfiguration des ninja WLAN erfolgreich."))

        except utils.AnsibleError as e:
            logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
            if state == 'yes':
                jobs.job_message(_("Starten des ninja WLAN fehlgeschlagen."))
            else:
                jobs.job_message(_("Stoppen des ninja WLAN fehlgeschlagen."))
    else:
        jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten."))


def toggle_silent(state):

    if state in ['yes', 'no']:
        try:
            if state == 'yes':
                jobs.job_message(_("silent WLAN wird gestartet..."))
            else:
                jobs.job_message(_("silent WLAN wird gestoppt..."))

            logger.debug("restarting silent")
            utils.exec_upri_config('enable_silent', state)
            utils.exec_upri_config('restart_silent')
            jobs.job_message(_("Konfiguration des silent WLAN erfolgreich."))

        except utils.AnsibleError as e:
            logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
            if state == 'yes':
                jobs.job_message(_("Starten des silent WLAN fehlgeschlagen."))
            else:
                jobs.job_message(_("Stoppen des silent WLAN fehlgeschlagen."))
    else:
        jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten."))