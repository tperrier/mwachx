# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AutomatedMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('priority', models.IntegerField(default=0)),
                ('english', models.TextField(blank=True)),
                ('swahili', models.TextField(blank=True)),
                ('luo', models.TextField(blank=True)),
                ('comment', models.TextField(blank=True)),
                ('group', models.CharField(max_length=10, choices=[(b'control', b'Control'), (b'one-way', b'One Way'), (b'two-way', b'Two Way')])),
                ('condition', models.CharField(max_length=10, choices=[(b'art', b'Starting ART'), (b'adolescent', b'Adolescent'), (b'first', b'First Time Mother'), (b'normal', b'Normal')])),
                ('hiv_messaging', models.BooleanField()),
                ('send_base', models.CharField(help_text=b'Base to send messages from', max_length=10, choices=[(b'edd', b'Before EDD'), (b'over', b'Post Dates'), (b'post', b'Postpartum'), (b'visit', b'Visit Messages'), (b'signup', b'From Signup'), (b'connect', b'Reconnect Messages')])),
                ('send_offset', models.IntegerField(default=0, help_text=b'Offset from base in weeks')),
                ('todo', models.BooleanField()),
            ],
        ),
    ]
