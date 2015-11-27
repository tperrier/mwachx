# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='topic',
            field=models.CharField(default=b'', help_text=b'The topic of this message', max_length=25, blank=True),
        ),
    ]
