# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
import subprocess
import time
from os import listdir
from os.path import exists, isfile, join

import dns.resolver
import netifaces as ni
import passwd
import redis as redisDB
from django import forms
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy
from netaddr import IPAddress

logger = logging.getLogger('uprilogger')


# function for debugging purposes
def get_local_facts():
    merged = {}
    if exists(settings.ANSIBLE_FACTS_DIR):
        for f in listdir(settings.ANSIBLE_FACTS_DIR):
            if isfile(join(settings.ANSIBLE_FACTS_DIR, f)) and f.endswith(".fact"):
                with open(join(settings.ANSIBLE_FACTS_DIR, f)) as data:
                    merged.update({f.replace(".fact", ""): json.load(data)})
    return merged


def get_defaults():
    try:
        with open(settings.DEFAULT_SETTINGS) as data:
            return json.load(data)
    except IOError as e:
        logger.error('Cannot read Default Settings File: ' + e.strerror)
        raise e


def get_fact(role, group, fact, defaults=True):
    if exists(settings.ANSIBLE_FACTS_DIR):
        try:
            with open(join(settings.ANSIBLE_FACTS_DIR, role + ".fact")) as file:
                data = json.load(file)
                return data[group][fact] if group in data and fact in data[group] else check_defaults(role, group, fact)
        except IOError as e:
            logger.debug('Cannot read Local Facts File ' + role + " :" + e.strerror)
            return check_defaults(role, group, fact) if defaults else None
    else:
        return check_defaults(role, group, fact) if defaults else None


def check_defaults(role, group, fact):
    data = get_defaults()
    return data[role][group][fact] if role in data and group in data[role] and fact in data[role][group] else None


def exec_upri_config(action, arg=''):
    # return 0 (success) if we are in development mode and upri-config script does not exist

    if settings.IGNORE_MISSING_UPRICONFIG and not exists('/usr/local/bin/upri-config.py'):
        time.sleep(1)
        return 0
    else:
        cmd = ['/usr/bin/sudo', '/usr/local/bin/upri-config.py', action]
        if arg:
            cmd.append(arg)
        rc = subprocess.call(cmd)

        # action_parse_logs returns code 1 if new entries have been added
        if rc > 1:
            raise AnsibleError('failed to execute action "%s" with argument "%s"' % (action, arg), rc)

        return rc


def check_passwords(password1, password2):
    if password1 and not password2:
        raise forms.ValidationError(ugettext_lazy("Bitte das Passwort zur Bestätigung erneut eingeben."))
        # print password1

    if password1 != password2:
        raise forms.ValidationError(ugettext_lazy("Die beiden Passwörter stimmen nicht überein."))

    pw2 = passwd.Password(password2)
    # password2 not empty string and valid
    if password2 and not pw2.is_valid():
        errors = []
        # if not pw2.has_digit():
        #     errors.append(forms.ValidationError(ugettext_lazy("Das Passwort muss mindestens 1 Ziffer beinhalten.")))
        # if not pw2.has_lowercase_char():
        #     errors.append(forms.ValidationError(ugettext_lazy("Das Passwort muss mindestens 1 Kleinbuchstaben beinhalten.")))
        # if not pw2.has_uppercase_char():
        #     errors.append(forms.ValidationError(ugettext_lazy("Das Passwort muss mindestens 1 Großbuchstaben beinhalten.")))
        # if not pw2.has_symbol():
        #     errors.append(forms.ValidationError(ugettext_lazy("Das Passwort muss mindestens 1 Sonderzeichen beinhalten.")))
        if not pw2.has_allowed_length():
            errors.append(forms.ValidationError(ugettext_lazy("Das Passwort muss zwischen 8 und 63 Zeichen lang sein.")))
        if not pw2.has_only_allowed_chars():
            errors.append(
                forms.ValidationError(ugettext_lazy("Das Passwort darf lediglich die Sonderzeichen %s enthalten." % pw2.get_allowed_chars()))
            )

        raise forms.ValidationError(errors)

    return password2


def secure_random_id(instance):
    return get_random_string(16)


def get_system_network_config():
    if_info = None
    interface = None
    try:
        interface = ni.gateways()['default'][ni.AF_INET][1]
        if_info = ni.ifaddresses(interface)
    except (ValueError, KeyError) as e:
        if interface:
            logger.warning("An error concerning the interface {} has occurred: {}".format(interface, str(e)))
        else:
            logger.warning("An error concerning the network configuration has occurred: {}".format(str(e)))
        return get_default_network_config()

    try:
        # get ip of specified interface
        ip = get_fact('interfaces', 'static', 'ip', defaults=False) or if_info[ni.AF_INET][-1]['addr']
    except IndexError:
        logger.debug("No IPv4 address is configured")
        ip = check_defaults('interfaces', 'static', 'ip')
    try:
        # get subnetmask of specified interface
        netmask = get_fact('interfaces', 'static', 'netmask', defaults=False) or if_info[ni.AF_INET][-1]['netmask'].split("/")[0]
    except IndexError:
        logger.debug("No IPv4 netmask is configured")
        netmask = check_defaults('interfaces', 'static', 'netmask')

    gw_default = False
    try:
        # get default gateway
        gateway = get_fact('interfaces', 'static', 'gateway', defaults=False) or ni.gateways()["default"][ni.AF_INET][0]
    except KeyError:
        logger.debug("No IPv4 default gateway is configured")
        gateway = check_defaults('interfaces', 'static', 'gateway')
        gw_default = True

    dns_servers = [get_fact('interfaces', 'static', 'dns', defaults=False)]
    if not dns_servers[0] and exists(settings.DNS_FILE):
        rs = dns.resolver.Resolver(filename=settings.DNS_FILE)
        # get all ipv4 nameservers
        dns_servers = [x for x in rs.nameservers if IPAddress(x).version == 4]
    else:
        if not gw_default:
            dns_servers = [gateway]
        else:
            check_defaults('interfaces', 'static', 'dns')

    # return ipv4 information
    return {'ip': ip, 'netmask': netmask, 'gateway': gateway, 'dns_servers': dns_servers}


def get_default_network_config():
    return {
        'ip': get_fact('interfaces', 'static', 'ip'),
        'netmask': get_fact('interfaces', 'static', 'netmask'),
        'gateway': get_fact('interfaces', 'static', 'gateway'),
        'dns_servers': [get_fact('interfaces', 'static', 'dns')]
    }


class AnsibleError(Exception):

    def __init__(self, message, rc):
        super(AnsibleError, self).__init__(message)
        self.rc = rc


def check_authorization(user):
    redis = redisDB.StrictRedis(host=settings.REDIS["HOST"], port=settings.REDIS["PORT"], db=settings.REDIS["DB"])
    return user.is_authenticated() or not redis.exists(settings.SETUP_DELIMITER.join((settings.SETUP_PREFIX, settings.SETUP_KEY)))
