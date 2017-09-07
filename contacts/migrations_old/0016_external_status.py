# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields

def set_external_status(apps, schema_editor):

    messages = apps.get_model('contacts','Message')

    # For all incoming messages
    for msg in messages.objects.filter(is_outgoing=True):
        if msg.external_data.get('status') is not None:
            msg.external_status = msg.external_data['status']
        msg.save()

def unset_external_status(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0015_auto_20160419_1803'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='external_status',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='contact',
            name='condition',
            field=models.CharField(default=b'normal', max_length=15, choices=[(b'art', b'1 - Starting ART'), (b'adolescent', b'2 - Adolescent'), (b'first', b'3 - First Time Mother'), (b'normal', b'4 -  Normal'), (b'multiple', b'5 - Twins')]),
        ),
        migrations.AlterField(
            model_name='contact',
            name='facility',
            field=models.CharField(max_length=15, choices=[(b'mathare', b'Mathare'), (b'bondo', b'Bondo'), (b'ahero', b'Ahero'), (b'siaya', b'Siaya'), (b'rachuonyo', b'Rachuonyo'), (b'riruta', b'Riruta')]),
        ),
        migrations.AlterField(
            model_name='message',
            name='external_data',
            field=jsonfield.fields.JSONField(blank=True),
        ),
        migrations.AlterField(
            model_name='practitioner',
            name='facility',
            field=models.CharField(max_length=15, choices=[(b'mathare', b'Mathare'), (b'bondo', b'Bondo'), (b'ahero', b'Ahero'), (b'siaya', b'Siaya'), (b'rachuonyo', b'Rachuonyo'), (b'riruta', b'Riruta')]),
        ),
        migrations.RunPython(set_external_status,unset_external_status)
    ]
