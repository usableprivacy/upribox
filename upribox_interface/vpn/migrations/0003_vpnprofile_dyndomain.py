# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vpn', '0002_auto_20150817_1005'),
    ]

    operations = [
        migrations.AddField(
            model_name='vpnprofile',
            name='dyndomain',
            field=models.CharField(default='', max_length=256),
            preserve_default=False,
        ),
    ]
