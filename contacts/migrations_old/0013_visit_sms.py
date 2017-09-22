# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0012_data_action_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='visit',
            name='missed_sms_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='visit',
            name='missed_sms_last_sent',
            field=models.DateField(default=None, null=True, blank=True),
        ),
    ]
