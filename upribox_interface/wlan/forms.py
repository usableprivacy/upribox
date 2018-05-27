# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy
from lib import passwd, ssid, utils


class WlanForm(forms.Form):
    ssid = forms.CharField(
        required=False,
        label=ugettext_lazy("SSID:"),
        max_length=100,
    )
    password1 = forms.CharField(
        required=False,
        label=ugettext_lazy("Neues Passwort:"),
        widget=forms.PasswordInput(attrs={'placeholder': '*' * 10}),
    )
    password2 = forms.CharField(
        required=False,
        label=ugettext_lazy("Passwort bestätigen:"),
        widget=forms.PasswordInput(attrs={'placeholder': '*' * 10}),
    )

    def __init__(self, ssid, *args, **kwargs):
        super(WlanForm, self).__init__(*args, **kwargs)
        self.fields['ssid'].widget.attrs['value'] = ssid

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        return utils.check_passwords(password1, password2)

    def clean_ssid(self):
        ssid_str = self.cleaned_data.get('ssid')

        errors = []
        check = ssid.SSID(ssid_str)

        if not check.is_valid():
            if not check.has_allowed_length():
                errors.append(forms.ValidationError(ugettext_lazy("Die SSID muss zwischen 1 und 32 Zeichen lang sein")))
            if not check.has_only_allowed_chars():
                errors.append(
                    forms.ValidationError(ugettext_lazy("Die SSID darf lediglich die Sonderzeichen %s enthalten" % check.get_allowed_chars()))
                )

            raise forms.ValidationError(errors)

        return ssid_str
