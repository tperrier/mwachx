# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0002_auto_20151127_0159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='connection',
            name='is_primary',
            field=models.BooleanField(default=False, verbose_name=b'Primary'),
        ),
        migrations.AlterField(
            model_name='message',
            name='external_success',
            field=models.NullBooleanField(verbose_name=b'Sent'),
        ),
        migrations.AlterField(
            model_name='message',
            name='is_outgoing',
            field=models.BooleanField(default=True, verbose_name=b'Out'),
        ),
        migrations.AlterField(
            model_name='message',
            name='is_system',
            field=models.BooleanField(default=True, verbose_name=b'System'),
        ),
        migrations.AlterField(
            model_name='message',
            name='is_viewed',
            field=models.BooleanField(default=False, verbose_name=b'Viewed'),
        ),
        migrations.AlterField(
            model_name='message',
            name='translation_status',
            field=models.CharField(default=b'todo', help_text=b'Status of translation', max_length=5, verbose_name=b'Translated', choices=[(b'todo', b'Todo'), (b'none', b'None'), (b'done', b'Done'), (b'auto', b'Auto')]),
        ),
    ]
