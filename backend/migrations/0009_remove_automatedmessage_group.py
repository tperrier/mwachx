# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0008_remove_automatedmessage_hiv_messaging'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='automatedmessage',
            name='group',
        ),
    ]
