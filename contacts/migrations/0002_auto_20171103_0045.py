# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='condition',
            field=models.CharField(default=b'normal', max_length=15, blank=True, choices=[(b'art', b'1 - Starting ART'), (b'adolescent', b'2 - Adolescent'), (b'first', b'3 - First Time Mother'), (b'normal', b'4 -  Normal'), (b'multiple', b'5 - Twins')]),
        ),
        migrations.AlterField(
            model_name='contact',
            name='hiv_messaging',
            field=models.CharField(default=b'none', max_length=15, verbose_name=b'HIV Messaging', blank=True, choices=[(b'none', b'No HIV Messaging'), (b'initiated', b'HIV Content If Initiated'), (b'system', b'HIV Content Allowed')]),
        ),
        migrations.AlterField(
            model_name='contact',
            name='study_group',
            field=models.CharField(blank=True, max_length=10, verbose_name=b'Group', choices=[(b'control', b'Control'), (b'one-way', b'One Way'), (b'two-way', b'Two Way')]),
        ),
    ]
