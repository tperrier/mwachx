# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0002_auto_20160122_1618'),
    ]

    operations = [
        migrations.AlterField(
            model_name='automatedmessage',
            name='send_base',
            field=models.CharField(help_text=b'Base to send messages from', max_length=20, choices=[(b'edd', b'Before EDD'), (b'over', b'Post Dates'), (b'dd', b'Postpartum'), (b'visit', b'Visit'), (b'signup', b'From Signup'), (b'connect', b'Reconnect'), (b'bounce', b'Bounce')]),
        ),
    ]
