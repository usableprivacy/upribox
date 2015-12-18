# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
import lib.utils


class Migration(migrations.Migration):

    dependencies = [
        ('vpn', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vpnprofile',
            name='download_slug',
            field=autoslug.fields.AutoSlugField(null=True, editable=False, populate_from=lib.utils.secure_random_id, always_update=True, unique=True),
        ),
        migrations.AddField(
            model_name='vpnprofile',
            name='download_valid_until',
            field=models.DateTimeField(null=True),
        ),
    ]
