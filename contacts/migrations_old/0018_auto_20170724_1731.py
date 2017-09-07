# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0017_exteral_status_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='external_status',
            field=models.CharField(blank=True, max_length=50, choices=[(b'', b'Received'), (b'Success', b'Success'), (b'Failed', b'Failed'), (b'Sent', b'Sent'), (b'Message Rejected By Gateway', b'Message Rejected By Gateway'), (b'Could Not Send', b'Could Not Send')]),
        ),
        migrations.AlterField(
            model_name='message',
            name='translation_status',
            field=models.CharField(default=b'todo', help_text=b'Status of translation', max_length=5, verbose_name=b'Translated', choices=[(b'todo', b'Todo'), (b'none', b'None'), (b'done', b'Done'), (b'auto', b'Auto'), (b'cust', b'Custom')]),
        ),
    ]
