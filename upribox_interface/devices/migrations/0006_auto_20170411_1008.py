# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0005_auto_20170411_1000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useragent',
            name='agent',
            field=models.TextField(unique=True),
        ),
    ]
