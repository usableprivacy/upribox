# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django import forms
from django.utils.translation import ugettext_lazy
from lib import domain
from lib.utils import get_fact

from .models import VpnProfile

logger = logging.getLogger('uprilogger')


class VpnProfileForm(forms.Form):

    profilename = forms.CharField(
        required=True,
        label=ugettext_lazy("Name:"),
        max_length=64,
    )

    dyndomain = forms.CharField(
        required=True,
        label=ugettext_lazy("Domain:"),
        max_length=64,
    )

    def __init__(self, *args, **kwargs):
        super(VpnProfileForm, self).__init__(*args, **kwargs)

        upri_dns_domain = None

        try:
            upri_dns_domain = get_fact('dns', 'dns', 'hostname')
        except:
            logger.error('Kein upri DNS fact gefunden.')

        if upri_dns_domain:
            self.fields['dyndomain'].widget = forms.HiddenInput()
            self.fields['dyndomain'].initial = upri_dns_domain
            self.fields['dyndomain'].label = ""

    def clean_profilename(self):
        profilename = self.cleaned_data['profilename']
        try:
            VpnProfile.objects.get(profilename=profilename)
            raise forms.ValidationError(ugettext_lazy("Profil existiert bereits"))
        except VpnProfile.DoesNotExist:
            return profilename

    def clean_dyndomain(self):

        dyndomain = self.cleaned_data['dyndomain']

        errors = []
        check = domain.Domain(dyndomain)

        if not check.is_valid():
            if not check.has_allowed_length():
                errors.append(forms.ValidationError(ugettext_lazy("Die Domain darf maximal 255 Zeichen lang sein")))
            if not check.has_only_allowed_chars():
                errors.append(forms.ValidationError(ugettext_lazy("Die Domain darf lediglich Buchstaben, Ziffern, Punkte und Minusse enthalten")))
            if not errors:
                errors.append(forms.ValidationError(ugettext_lazy("Die Domain ist nicht gültig")))

            raise forms.ValidationError(errors)

        return check.get_match()  #dyndomain
