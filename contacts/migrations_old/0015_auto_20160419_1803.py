# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0014_loss_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='condition',
            field=models.CharField(default=b'normal', max_length=15, choices=[(b'art', b'1 - Starting ART'), (b'adolescent', b'2 - Adolescent'), (b'first', b'3 - First Time Mother'), (b'normal', b'4 -  Normal')]),
        ),
        migrations.AlterField(
            model_name='contact',
            name='delivery_source',
            field=models.CharField(blank=True, max_length=10, verbose_name=b'Delivery Notification Source', choices=[(b'phone', b'Phone'), (b'sms', b'SMS'), (b'visit', b'Clinic Visit'), (b'm2m', b'Mothers to Mothers'), (b'other', b'Other')]),
        ),
        migrations.AlterField(
            model_name='contact',
            name='status',
            field=models.CharField(default=b'pregnant', max_length=15, choices=[(b'pregnant', b'Pregnant'), (b'over', b'Post-Date'), (b'post', b'Post-Partum'), (b'ccc', b'CCC'), (b'completed', b'Completed'), (b'stopped', b'Withdrew'), (b'loss', b'SAE opt-in'), (b'sae', b'SAE opt-out'), (b'other', b'Admin Stop'), (b'quit', b'Left Study')]),
        ),
        migrations.AlterField(
            model_name='visit',
            name='visit_type',
            field=models.CharField(default=b'clinic', max_length=25, choices=[(b'clinic', b'Clinic Visit'), (b'study', b'Study Visit'), (b'both', b'Both'), (b'delivery', b'Delivery')]),
        ),
    ]
