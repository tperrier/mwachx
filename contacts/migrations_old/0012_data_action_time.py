# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def set_action_time(apps, schema_editor):

    messages = apps.get_model('contacts','Message')

    # For all incoming messages
    for msg in messages.objects.filter(is_outgoing=False):
        if msg.is_viewed:
            if msg.parent is None:
                msg.action_time = msg.modified
            else:
                msg.action_time = msg.parent.created
        msg.save()

def unset_action_time(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0011_message_action_time'),
    ]

    operations = [
        migrations.RunPython(set_action_time,unset_action_time),
    ]
