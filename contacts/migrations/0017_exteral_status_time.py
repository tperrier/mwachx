# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0016_external_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='external_success_time',
            field=models.DateTimeField(default=None, null=True, blank=True),
        ),
    ]
