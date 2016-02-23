# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0007_auto_delete_skipped'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='translation_time',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
