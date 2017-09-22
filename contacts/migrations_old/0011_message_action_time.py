# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0010_data_last_msg'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='action_time',
            field=models.DateTimeField(default=None, null=True, blank=True),
        ),
    ]
