# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def set_last_msg_times(apps, schema_editor):
    ''' Set last_msg dates based on call history '''
    contacts = apps.get_model('contacts','Contact')

    for c in contacts.objects.all():
        last_msg_client = c.message_set.filter(is_outgoing=False).first()
        last_msg_system = c.message_set.filter(is_system=True).first()

        if last_msg_client:
            c.last_msg_client = last_msg_client.created.date()
        if last_msg_system:
            c.last_msg_system = last_msg_system.created.date()
        c.save()

def unset_last_msg_times(apps, schema_editor):
    ''' Do nothing on reverse data migration '''
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0009_data_translation_time'),
    ]

    operations = [
        migrations.RunPython(set_last_msg_times,unset_last_msg_times),
    ]
