# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='automatedmessage',
            name='condition',
            field=models.CharField(max_length=20, choices=[(b'art', b'Starting ART'), (b'adolescent', b'Adolescent'), (b'first', b'First Time Mother'), (b'normal', b'Normal')]),
        ),
        migrations.AlterField(
            model_name='automatedmessage',
            name='group',
            field=models.CharField(max_length=20, choices=[(b'control', b'Control'), (b'one-way', b'One Way'), (b'two-way', b'Two Way')]),
        ),
        migrations.AlterField(
            model_name='automatedmessage',
            name='send_base',
            field=models.CharField(help_text=b'Base to send messages from', max_length=20, choices=[(b'edd', b'Before EDD'), (b'over', b'Post Dates'), (b'post', b'Postpartum'), (b'visit', b'Visit Messages'), (b'signup', b'From Signup'), (b'connect', b'Reconnect Messages')]),
        ),
    ]
