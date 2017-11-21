# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0007_auto_20171025_0022'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='automatedmessage',
            name='hiv_messaging',
        ),
    ]
