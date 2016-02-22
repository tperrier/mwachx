# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import itertools as it

from django.db import models, migrations

def convert_status(apps, schema_editor):
    ''' Migrate Visit.skipped and ScheduledPhoneCall.skipped -> status
        (pending,missed,deleted,attended)
    '''

    Visit = apps.get_model("contacts","Visit")
    ScheduledPhoneCall = apps.get_model("contacts","ScheduledPhoneCall")

    for obj in it.chain(Visit.objects.all(), ScheduledPhoneCall.objects.all()):
        if obj.skipped is None:
            obj.status = 'pending'
        elif obj.skipped == False:
            obj.status = 'attended'
        elif obj.skipped == True:
            obj.status = 'missed'
        obj.save()

def unconvert_status(apps, schema_editor):
    ''' Reverse function sets skipped based on status'''

    Visit = apps.get_model("contacts","Visit")
    ScheduledPhoneCall = apps.get_model("contacts","ScheduledPhoneCall")

    for obj in it.chain(Visit.objects.all(), ScheduledPhoneCall.objects.all()):
        if obj.status == 'pending':
            obj.skipped = None
        elif obj.status == 'attended':
            obj.skipped = False
        elif obj.status == 'missed':
            obj.skipped = True
        obj.save()

class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0005_auto_add_visit_status'),
    ]

    operations = [
        migrations.RunPython(convert_status,unconvert_status),
    ]
