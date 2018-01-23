# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0002_auto_20171121_1035'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='prep_initiation',
            field=models.DateField(null=True, verbose_name=b'PrEP Initiation Date', blank=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='due_date',
            field=models.DateField(null=True, verbose_name=b'Estimated Delivery Date', blank=True),
        ),
    ]
