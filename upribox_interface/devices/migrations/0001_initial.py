# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DeviceEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip', models.CharField(unique=True, max_length=20)),
                ('mac', models.CharField(max_length=20, null=True)),
                ('dhcp_fingerprint', models.CharField(max_length=256, null=True)),
                ('dhcp_vendor', models.CharField(max_length=256, null=True)),
                ('user_agent', models.CharField(max_length=256, null=True)),
                ('hostname', models.CharField(max_length=256, null=True)),
                ('device_name', models.CharField(max_length=256, null=True)),
                # ('final', models.BooleanField(default=False)),
            ],
        ),
        migrations.RunSQL('alter table devices_deviceentry add column final bool NOT NULL default 0')
    ]
