# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ForwardMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('identity', models.CharField(max_length=25)),
                ('text', models.TextField(help_text=b'Text of the SMS message')),
                ('transport', models.CharField(help_text=b'Transport name', max_length=25)),
                ('fwrd_status', models.CharField(help_text=b'Forward Status', max_length=25, choices=[(b'success', b'Success'), (b'failed', b'Failed'), (b'none', b'No Forward In Transport')])),
                ('url', models.CharField(help_text=b'Forward URL', max_length=250)),
                ('external_id', models.CharField(max_length=50, blank=True)),
                ('external_data', jsonfield.fields.JSONField(blank=True)),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
    ]
