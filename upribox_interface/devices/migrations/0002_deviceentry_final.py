# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='deviceentry',
            name='final',
            field=models.BooleanField(default=False),
        ),
    ]

    def apply(self, project_state, schema_editor, collect_sql=False):
        self.operations = []
        super(Migration, self).apply(project_state, schema_editor, collect_sql)
