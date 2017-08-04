# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

import lib.jobs as jobs
import lib.utils as utils
from django.utils.translation import ugettext as _

logger = logging.getLogger('uprilogger')


def toggle_vpn(state):
    try:
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
                raise
        else:
            jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten."))
            raise jobs.JobFailedError()
    except Exception as e:
        logger.exception(e)
        jobs.job_clear_messages()
        jobs.job_message(_("Konfiguration des VPNs fehlgeschlagen."))
        raise jobs.JobFailedError()


def generate_profile(profile_id):
    try:
        try:
            jobs.job_message(_("VPN Profile wird generiert..."))
            logger.debug("generating vpn profile")
            utils.exec_upri_config('generate_profile', profile_id)
            jobs.job_message(_("Generieren des VPN Profiles erfolgreich."))

        except utils.AnsibleError as e:
            logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
            raise
            # jobs.job_message(_("Generieren des VPN Profiles fehlgeschlagen."))
            #profile = VpnProfile.objects.get(id=profile_id)
            #profile.delete()
    except Exception as e:
        logger.exception(e)
        jobs.job_clear_messages()
        jobs.job_message(_("Generieren des VPN Profiles fehlgeschlagen."))
        raise jobs.JobFailedError()


def delete_profile(profile_id):
    try:
        try:
            jobs.job_message(_("VPN Profile wird entfernt..."))
            logger.debug("deleting vpn profile")
            utils.exec_upri_config('delete_profile', profile_id)
            jobs.job_message(_("Entfernen des VPN Profiles erfolgreich."))

        except utils.AnsibleError as e:
            logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
            # jobs.job_message(_("Entfernen des VPN Profiles fehlgeschlagen."))
            raise

    except Exception as e:
        logger.exception(e)
        jobs.job_clear_messages()
        jobs.job_message(_("Entfernen des VPN Profiles fehlgeschlagen."))
        raise jobs.JobFailedError()
