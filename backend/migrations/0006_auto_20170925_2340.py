# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

forwardSQL = "update backend_automatedmessage set send_offset = send_offset * 7;"

backwardSQL = "update backend_automatedmessage set send_offset = send_offset / 7;"


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0005_auto_20160419_1803'),
    ]

    operations = [
        migrations.RunSQL(forwardSQL, backwardSQL)
    ]
