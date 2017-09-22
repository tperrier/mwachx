# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0013_visit_sms'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='loss_date',
            field=models.DateField(help_text=b'SAE date if applicable', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='condition',
            field=models.CharField(default=b'normal', max_length=15, choices=[(b'art', b'1 - Starting ART'), (b'adolescent', b'2 - Adolescent'), (b'first', b'3 - First Time Mother'), (b'normal', b'4 -  Normal'), (b'nbaby', b'SAE Track')]),
        ),
        migrations.AlterField(
            model_name='contact',
            name='status',
            field=models.CharField(default=b'pregnant', max_length=15, choices=[(b'pregnant', b'Pregnant'), (b'over', b'Post-Date'), (b'post', b'Post-Partum'), (b'ccc', b'CCC'), (b'completed', b'Completed'), (b'stopped', b'Withdrew'), (b'loss', b'SAE opt-in'), (b'other', b'Stopped Other')]),
        ),
    ]
