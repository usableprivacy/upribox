# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

import lib.jobs as jobs
import lib.utils as utils
from django.utils.translation import ugettext as _

logger = logging.getLogger('uprilogger')


def reconfigure_network(ip, netmask, gateway, dns, enable=False):
    try:
        jobs.job_message(_("Die Netzwerkeinstellungen werden neu konfiguriert..."))
        try:
            if enable:
                logger.debug("Static IP activated")
                logger.debug(enable)
                jobs.job_message(_("Modus zur Vergabe statischer IP Adressen wird aktiviert..."))
                utils.exec_upri_config('enable_static_ip', "yes")
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
                if utils.get_fact('interfaces', 'general', 'mode') == "static":
                    jobs.job_message(_("Netzwerk wird neu gestartet..."))
                    logger.debug("restarting network")
                    utils.exec_upri_config('restart_network')

            jobs.job_message(_("Konfiguration der Netzwerkeinstellungen erfolgreich."))

        except utils.AnsibleError as e:
            logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
            # jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten. Fehlercode: %(errorcode)s" % {'errorcode': e.rc}))
            raise
    except Exception as e:
        logger.exception(e)
        # jobs.job_clear_messages()
        jobs.job_error(_("Konfiguration der Netzwerkeinstellungen fehlgeschlagen."))
        raise jobs.JobFailedError()


def toggle_ssh(state):
    try:
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
                raise
        else:
            # jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten."))
            logger.error("something unexpected happened")
            raise jobs.JobFailedError()
    except Exception as e:
        logger.exception(e)
        # jobs.job_clear_messages()
        jobs.job_error(_("Konfiguration von SSH fehlgeschlagen."))
        raise jobs.JobFailedError()


def toggle_apate(state, messages=True):
    try:
        if state in ['yes', 'no']:
            try:
                if state == 'yes':
                    if messages:
                        jobs.job_message(_("Apate ARP Spoofing Daemon wird gestartet..."))
                else:
                    if messages:
                        jobs.job_message(_("Apate ARP Spoofing Daemon wird gestoppt..."))

                logger.debug("restarting apate")
                utils.exec_upri_config('enable_apate', state)
                utils.exec_upri_config('restart_apate')
                if messages:
                    jobs.job_message(_("Konfiguration von Apate ARP Spoofing Daemon erfolgreich."))

            except utils.AnsibleError as e:
                logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
                raise

        else:
            logger.error("something unexpected happened")
            raise jobs.JobFailedError()

    except Exception as e:
        logger.exception(e)
        # jobs.job_clear_messages()
        jobs.job_error(_("Konfiguration von Apate ARP Spoofing Daemon fehlgeschlagen."))
        raise jobs.JobFailedError()


def toggle_static(state):
    try:
        if state in ['no', 'yes']:
            try:
                if state == 'yes':
                    jobs.job_message(_("Statische IP wird aktiviert..."))
                else:
                    jobs.job_message(_("Statische IP wird deaktiviert..."))

                logger.debug("restarting network")
                utils.exec_upri_config('enable_static_ip', state)
                utils.exec_upri_config('restart_network')
                jobs.job_message(_("Konfiguration der statischen IP erfolgreich."))

            except utils.AnsibleError as e:
                logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
                raise
        else:
            logger.error("something unexpected happened")
            raise jobs.JobFailedError()

    except Exception as e:
        logger.exception(e)
        # jobs.job_clear_messages()
        jobs.job_error(_("Konfiguration der statischen IP fehlgeschlagen."))
        raise jobs.JobFailedError()


def toggle_dhcpd(state):
    try:
        if state in ['no', 'yes']:
            try:
                logger.debug("dhcp server: %s" % state)
                if state == 'yes':
                    jobs.job_message(_("DHCP Server wird aktiviert..."))
                else:
                    jobs.job_message(_("DHCP Server wird deaktiviert..."))
                utils.exec_upri_config('set_dhcpd', state)

                jobs.job_message(_("DHCP Server wird konfiguriert..."))
                utils.exec_upri_config('restart_dhcpd')
                jobs.job_message(_("Konfiguration des DHCP Servers erfolgreich."))

            except utils.AnsibleError as e:
                logger.error("ansible failed with error %d: %s" % (e.rc, e.message))
                raise
        else:
            jobs.job_message(_("Es ist ein unbekannter Fehler aufgetreten."))
            raise jobs.JobFailedError()

    except Exception as e:
        logger.exception(e)
        # jobs.job_clear_messages()
        jobs.job_error(_("Konfiguration des DHCP Servers fehlgeschlagen."))
        raise jobs.JobFailedError()
