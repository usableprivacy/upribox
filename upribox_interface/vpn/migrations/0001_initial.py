# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
import lib.utils


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='VpnProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('profilename', models.CharField(max_length=32)),
                ('config', models.TextField()),
                ('creation_date', models.DateField(auto_now_add=True)),
                ('slug', autoslug.fields.AutoSlugField(populate_from=lib.utils.secure_random_id, unique=True, editable=False)),
            ],
            options={
                'ordering': ['creation_date'],
            },
        ),
    ]
