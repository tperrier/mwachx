# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0003_auto_20160121_2043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scheduledphonecall',
            name='notification_last_seen',
            field=models.DateField(default=None, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='visit',
            name='notification_last_seen',
            field=models.DateField(default=None, null=True, blank=True),
        ),
    ]
