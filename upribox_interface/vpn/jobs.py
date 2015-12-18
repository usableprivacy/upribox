# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import lib.jobs as jobs
import lib.utils as utils
from django.utils.translation import ugettext as _
import logging
from .models import VpnProfile
import requests

logger = logging.getLogger('uprilogger')

def toggle_vpn(state):
    if state in ['yes', 'no']:
        try:
            if state == 'yes':
                jobs.job_message(_("VPN wird gestartet..."))
            else:
                jobs.job_message(_("VPN wird gestoppt..."))

            # Restart VPN
            logger.debug("restarting vpn")
            utils.exec_upri_config('enable_vpn', state)
            utils.exec_upri_config('restart_vpn')
            jobs.job_message(_("Konfiguration des VPNs erfolgreich."))

        except utils.AnsibleError as e:
            logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
            if state == 'yes':
                jobs.job_message(_("Starten des VPNs fehlgeschlagen."))
            else:
                jobs.job_message(_("Stoppen des VPNs fehlgeschlagen."))
    else:
        jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten."))


def generate_profile(profile_id):
    try:
        jobs.job_message(_("VPN Profile wird generiert..."))
        logger.debug("generating vpn profile")
        utils.exec_upri_config('generate_profile', profile_id)
        jobs.job_message(_("Generieren des VPN Profiles erfolgreich."))

    except utils.AnsibleError as e:
        logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
        jobs.job_message(_("Generieren des VPN Profiles fehlgeschlagen."))
        #profile = VpnProfile.objects.get(id=profile_id)
        #profile.delete()

def delete_profile(profile_id):
    try:
        jobs.job_message(_("VPN Profile wird entfernt..."))
        logger.debug("deleting vpn profile")
        utils.exec_upri_config('delete_profile', profile_id)
        jobs.job_message(_("Entfernen des VPN Profiles erfolgreich."))

    except utils.AnsibleError as e:
        logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
        jobs.job_message(_("Entfernen des VPN Profiles fehlgeschlagen."))
