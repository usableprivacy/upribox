# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import lib.jobs as jobs
import lib.utils as utils
from django.utils.translation import ugettext as _
import logging
logger = logging.getLogger('uprilogger')

def reconfigure_network(ip, netmask, gateway, dns):

    jobs.job_message(_("Die Netzwerkeinstellungen werden neu konfiguriert..."))
    try:
        if ip:
            logger.debug("new IP: %s" % ip)
            jobs.job_message(_("IP Adresse wird geändert..."))
            utils.exec_upri_config('set_ip', ip)
        if netmask:
            logger.debug("new netmask: %s" % netmask)
            jobs.job_message(_("Subnetzmaske wird geändert..."))
            utils.exec_upri_config('set_netmask', netmask)
        if gateway:
            logger.debug("new gateway: %s" % gateway)
            jobs.job_message(_("Gateway wird geändert..."))
            utils.exec_upri_config('set_gateway', gateway)
        if dns:
            logger.debug("new dns server: %s" % dns)
            jobs.job_message(_("DNS Server wird geändert..."))
            utils.exec_upri_config('set_dns_server', dns)
        if ip or netmask or gateway or dns:
            jobs.job_message(_("Netzwerk wird neu gestartet..."))
            logger.debug("restarting network")
            # utils.exec_upri_config('restart_network')

        jobs.job_message(_("Konfiguration erfolgreich"))

    except utils.AnsibleError as e:
        logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
        jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten. Fehlercode: %(errorcode)s" % {'errorcode': e.rc}))

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
