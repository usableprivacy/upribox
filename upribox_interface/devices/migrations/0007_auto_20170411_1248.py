# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0006_auto_20170411_1008'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deviceentry',
            name='device_name',
        ),
        migrations.AddField(
            model_name='useragent',
            name='model',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
