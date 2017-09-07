# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def set_translation_time(apps, schema_editor):
    ''' Data migration for translation time. Set to modified time if
        translation_status is none or done
    '''

    Message = apps.get_model('contacts','Message')
    for msg in Message.objects.all():
        if msg.is_outgoing == False and msg.translation_status in ('none','done'):
            msg.translation_time = msg.modified
            msg.save()

def unset_translation_time(apps, schema_editor):
    ''' Do nothing on reverse data migration '''
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0008_add_translation_time'),
    ]

    operations = [
        migrations.RunPython(set_translation_time,unset_translation_time),
    ]
