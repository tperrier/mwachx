# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0003_auto_20160206_1558'),
    ]

    operations = [
        migrations.AlterField(
            model_name='automatedmessage',
            name='condition',
            field=models.CharField(max_length=20, choices=[(b'art', b'Starting ART'), (b'adolescent', b'Adolescent'), (b'first', b'First Time Mother'), (b'normal', b'Normal'), (b'nbaby', b'No Baby')]),
        ),
        migrations.AlterField(
            model_name='automatedmessage',
            name='send_base',
            field=models.CharField(help_text=b'Base to send messages from', max_length=20, choices=[(b'edd', b'Before EDD'), (b'over', b'Post Dates'), (b'dd', b'Postpartum'), (b'visit', b'Visit'), (b'signup', b'From Signup'), (b'connect', b'Reconnect'), (b'bounce', b'Bounce'), (b'loss', b'Loss')]),
        ),
    ]
