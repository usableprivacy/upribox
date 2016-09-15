# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
from os import listdir
from os.path import isfile, join, exists
import logging
from django.conf import settings
import subprocess
import time
import passwd
from django.utils.translation import ugettext_lazy
from django import forms
from django.utils.crypto import get_random_string

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


def get_fact(role, group, fact):
    if exists(settings.ANSIBLE_FACTS_DIR):
        try:
            with open(join(settings.ANSIBLE_FACTS_DIR, role + ".fact")) as file:
                data = json.load(file)
                return data[group][fact] if group in data and fact in data[group] else check_defaults(role, group, fact)
        except IOError as e:
            logger.debug('Cannot read Local Facts File ' + role + " :" + e.strerror)
            return check_defaults(role, group, fact)
    else:
        return check_defaults(role, group, fact)


def check_defaults(role, group, fact):
    data = get_defaults()
    return data[role][group][fact] if role in data and group in data[role] and fact in data[role][group] else None


def exec_upri_config(action, arg=''):
    # return 0 (success) if we are in development mode and upri-config script does not exist

    if settings.IGNORE_MISSING_UPRICONFIG and not exists('/usr/local/bin/upri-config.py'):
        time.sleep(1)
        return 0
    else:
        rc = subprocess.call(['/usr/bin/sudo', '/usr/local/bin/upri-config.py', action, arg])

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
    #password2 not empty string and valid
    if password2 and not pw2.is_valid():
        errors = []
        if not pw2.has_digit():
            errors.append(forms.ValidationError(ugettext_lazy("Das Passwort muss mindestens 1 Ziffer beinhalten.")))
        if not pw2.has_lowercase_char():
            errors.append(
                forms.ValidationError(ugettext_lazy("Das Passwort muss mindestens 1 Kleinbuchstaben beinhalten.")))
        if not pw2.has_uppercase_char():
            errors.append(
                forms.ValidationError(ugettext_lazy("Das Passwort muss mindestens 1 Großbuchstaben beinhalten.")))
        if not pw2.has_symbol():
            errors.append(
                forms.ValidationError(ugettext_lazy("Das Passwort muss mindestens 1 Sonderzeichen beinhalten.")))
        if not pw2.has_allowed_length():
            errors.append(forms.ValidationError(ugettext_lazy("Das Passwort muss zwischen 8 und 63 Zeichen lang sein.")))
        if not pw2.has_only_allowed_chars():
            errors.append(forms.ValidationError(ugettext_lazy(
                    "Das Passwort darf lediglich die Sonderzeichen %s enthalten." % pw2.get_allowed_chars())))


        raise forms.ValidationError(errors)

    return password2


def secure_random_id(instance):
    return get_random_string(16)

class AnsibleError(Exception):
    def __init__(self, message, rc):
        super(AnsibleError, self).__init__(message)
        self.rc = rc
