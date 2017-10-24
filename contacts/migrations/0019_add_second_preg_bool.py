# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0018_auto_20170724_1731'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='second_preg',
            field=models.BooleanField(default=False, verbose_name=b'Second Pregnancy'),
        ),
        migrations.AlterField(
            model_name='message',
            name='external_success',
            field=models.NullBooleanField(verbose_name=b'Success'),
        ),
    ]
