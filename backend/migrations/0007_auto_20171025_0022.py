# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0006_auto_20170925_2340'),
    ]

    operations = [
        migrations.AlterField(
            model_name='automatedmessage',
            name='send_offset',
            field=models.IntegerField(default=0, help_text=b'Offset from base in days'),
        ),
    ]
