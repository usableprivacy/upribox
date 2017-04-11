# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0002_deviceentry_final'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deviceentry',
            name='ip',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='deviceentry',
            name='mac',
            field=models.CharField(default='00:00:00:00:00:00', unique=True, max_length=20),
            preserve_default=False,
        ),
    ]
