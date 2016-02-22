# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0006_data_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scheduledphonecall',
            name='skipped',
        ),
        migrations.RemoveField(
            model_name='visit',
            name='skipped',
        ),
        migrations.AlterField(
            model_name='scheduledphonecall',
            name='status',
            field=models.CharField(default=b'pending', help_text=b'current status of event', max_length=15, choices=[(b'pending', b'Pending'), (b'missed', b'Missed'), (b'deleted', b'Deleted'), (b'attended', b'Attended')]),
        ),
        migrations.AlterField(
            model_name='visit',
            name='status',
            field=models.CharField(default=b'pending', help_text=b'current status of event', max_length=15, choices=[(b'pending', b'Pending'), (b'missed', b'Missed'), (b'deleted', b'Deleted'), (b'attended', b'Attended')]),
        ),
    ]
