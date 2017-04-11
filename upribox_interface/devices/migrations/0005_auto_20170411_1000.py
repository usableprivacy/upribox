# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0004_auto_20170406_1334'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAgent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('agent', models.TextField()),
            ],
        ),
        migrations.RemoveField(
            model_name='deviceentry',
            name='score',
        ),
        migrations.RemoveField(
            model_name='deviceentry',
            name='user_agent',
        ),
        migrations.AddField(
            model_name='deviceentry',
            name='user_agent',
            field=models.ManyToManyField(to='devices.UserAgent'),
        ),
    ]
