# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0004_auto_20160206_1558'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduledphonecall',
            name='status',
            field=models.CharField(default=b'pending', help_text=b'current status of event', max_length=15, choices=[(b'pending', b'Pending'), (b'missed', b'Missed'), (b'deleted', b'Deleted')]),
        ),
        migrations.AddField(
            model_name='visit',
            name='status',
            field=models.CharField(default=b'pending', help_text=b'current status of event', max_length=15, choices=[(b'pending', b'Pending'), (b'missed', b'Missed'), (b'deleted', b'Deleted')]),
        ),
        migrations.AlterField(
            model_name='visit',
            name='visit_type',
            field=models.CharField(default=b'clinic', max_length=25, choices=[(b'clinic', b'Clinic Visit'), (b'study', b'Study Visit'), (b'both', b'Both')]),
        ),
    ]
