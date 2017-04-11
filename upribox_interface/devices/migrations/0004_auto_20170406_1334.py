# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0003_auto_20170406_1217'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deviceentry',
            name='final',
        ),
        migrations.AddField(
            model_name='deviceentry',
            name='score',
            field=models.IntegerField(null=True),
        ),
    ]
