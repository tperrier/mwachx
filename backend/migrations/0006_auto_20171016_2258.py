# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0005_auto_20160419_1803'),
    ]

    operations = [
        migrations.AlterField(
            model_name='automatedmessage',
            name='condition',
            field=models.CharField(max_length=20, choices=[(b'art', b'Starting ART'), (b'adolescent', b'Adolescent'), (b'first', b'First Time Mother'), (b'normal', b'Normal'), (b'nbaby', b'No Baby'), (b'preg2', b'Second')]),
        ),
    ]
