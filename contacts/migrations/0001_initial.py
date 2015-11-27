# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Connection',
            fields=[
                ('identity', models.CharField(max_length=25, serialize=False, primary_key=True)),
                ('description', models.CharField(help_text=b'Description of phone numbers relationship to contact', max_length=30, null=True, blank=True)),
                ('is_primary', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('study_id', models.CharField(help_text=b'* Use Barcode Scanner', unique=True, max_length=10, verbose_name=b'Study ID')),
                ('anc_num', models.CharField(max_length=15, verbose_name=b'ANC #')),
                ('ccc_num', models.CharField(max_length=15, null=True, verbose_name=b'CCC #', blank=True)),
                ('facility', models.CharField(max_length=15, choices=[(b'mathare', b'Mathare'), (b'bondo', b'Bondo'), (b'ahero', b'Ahero')])),
                ('study_group', models.CharField(max_length=10, verbose_name=b'Group', choices=[(b'control', b'Control'), (b'one-way', b'One Way'), (b'two-way', b'Two Way')])),
                ('send_day', models.IntegerField(default=0, verbose_name=b'Send Day', choices=[(0, b'Monday'), (1, b'Tuesday'), (2, b'Wednesday'), (3, b'Thursday'), (4, b'Friday'), (5, b'Satuday'), (6, b'Sunday')])),
                ('send_time', models.IntegerField(default=8, verbose_name=b'Send Time', choices=[(8, b'Morning (8 AM)'), (13, b'Afternoon (1 PM)'), (20, b'Evening (8 PM)')])),
                ('nickname', models.CharField(max_length=20)),
                ('birthdate', models.DateField(verbose_name=b'DOB')),
                ('partner_name', models.CharField(max_length=40, verbose_name=b'Partner Name', blank=True)),
                ('relationship_status', models.CharField(blank=True, max_length=15, verbose_name=b'Relationship Status', choices=[(b'single', b'Single'), (b'partner', b'Partner'), (b'married', b'Married'), (b'seperated', b'Seperated')])),
                ('previous_pregnancies', models.IntegerField(help_text=b'* excluding current', null=True, blank=True)),
                ('phone_shared', models.NullBooleanField(verbose_name=b'Phone Shared')),
                ('status', models.CharField(default=b'pregnant', max_length=15, choices=[(b'pregnant', b'Pregnant'), (b'over', b'Post-Date'), (b'post', b'Post-Partum'), (b'ccc', b'CCC'), (b'completed', b'Completed'), (b'stopped', b'Withdrew'), (b'other', b'Stopped Other')])),
                ('language', models.CharField(default=b'english', max_length=10, choices=[(b'english', b'English'), (b'luo', b'Luo'), (b'swahili', b'Swahili')])),
                ('condition', models.CharField(default=b'normal', max_length=15, choices=[(b'art', b'1 - Starting ART'), (b'adolescent', b'2 - Adolescent'), (b'first', b'3 - First Time Mother'), (b'normal', b'4 -  Normal')])),
                ('due_date', models.DateField(verbose_name=b'Estimated Delivery Date')),
                ('delivery_date', models.DateField(null=True, verbose_name=b'Delivery Date', blank=True)),
                ('delivery_source', models.CharField(blank=True, max_length=10, verbose_name=b'Delivery Notification Source', choices=[(b'phone', b'Phone'), (b'sms', b'SMS'), (b'visit', b'Clinic Visit'), (b'other', b'Other')])),
                ('art_initiation', models.DateField(help_text=b'Date of ART Initiation', null=True, verbose_name=b'ART Initiation', blank=True)),
                ('hiv_disclosed', models.NullBooleanField(verbose_name=b'HIV Disclosed')),
                ('hiv_messaging', models.CharField(default=b'none', max_length=15, verbose_name=b'HIV Messaging', choices=[(b'none', b'No HIV Messaging'), (b'initiated', b'HIV Content If Initiated'), (b'system', b'HIV Content Allowed')])),
                ('child_hiv_status', models.NullBooleanField(verbose_name=b'Child HIV Status')),
                ('family_planning', models.CharField(blank=True, max_length=10, verbose_name=b'Family Planning', choices=[(b'none', b'None'), (b'iud', b'IUD'), (b'pill', b'Pills'), (b'depot', b'Depot'), (b'implant', b'Implant')])),
                ('last_msg_client', models.DateField(help_text=b'Date of last client message received', null=True, editable=False, blank=True)),
                ('last_msg_system', models.DateField(help_text=b'Date of last system message sent', null=True, editable=False, blank=True)),
                ('is_validated', models.BooleanField(default=False)),
                ('validation_key', models.CharField(max_length=5, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='EventLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('event', models.CharField(help_text=b'Event Name', max_length=25)),
                ('data', jsonfield.fields.JSONField()),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('text', models.TextField(help_text=b'Text of the SMS message')),
                ('is_outgoing', models.BooleanField(default=True)),
                ('is_system', models.BooleanField(default=True)),
                ('is_viewed', models.BooleanField(default=False)),
                ('is_related', models.NullBooleanField(default=None)),
                ('translated_text', models.TextField(default=b'', help_text=b'Text of the translated message', max_length=1000, blank=True)),
                ('translation_status', models.CharField(default=b'todo', help_text=b'Status of translation', max_length=5, choices=[(b'todo', b'Todo'), (b'none', b'None'), (b'done', b'Done'), (b'auto', b'Auto')])),
                ('languages', models.CharField(default=b'', help_text=b'Semi colon seperated list of languages', max_length=50, blank=True)),
                ('topic', models.CharField(default=b'', help_text=b'The topic of this message', max_length=10, blank=True)),
                ('external_id', models.CharField(max_length=50, blank=True)),
                ('external_success', models.NullBooleanField()),
                ('external_data', jsonfield.fields.JSONField()),
                ('auto', models.CharField(max_length=50, blank=True)),
                ('admin_user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('connection', models.ForeignKey(to='contacts.Connection')),
                ('contact', models.ForeignKey(blank=True, to='contacts.Contact', null=True)),
                ('parent', models.ForeignKey(related_name='replies', blank=True, to='contacts.Message', null=True)),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('comment', models.TextField(blank=True)),
                ('admin', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('participant', models.ForeignKey(to='contacts.Contact')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='PhoneCall',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_outgoing', models.BooleanField(default=False)),
                ('outcome', models.CharField(default=b'answered', max_length=10, choices=[(b'no_ring', b'No Ring'), (b'no_answer', b'No Answer'), (b'answered', b'Answered')])),
                ('length', models.IntegerField(null=True, blank=True)),
                ('comment', models.TextField(null=True, blank=True)),
                ('admin_user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('connection', models.ForeignKey(to='contacts.Connection')),
                ('contact', models.ForeignKey(to='contacts.Contact')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Practitioner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('facility', models.CharField(max_length=15, choices=[(b'mathare', b'Mathare'), (b'bondo', b'Bondo'), (b'ahero', b'Ahero')])),
                ('password_changed', models.BooleanField(default=False)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ScheduledPhoneCall',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('scheduled', models.DateField()),
                ('arrived', models.DateField(default=None, null=True, blank=True)),
                ('notification_last_seen', models.DateField(default=None, null=True)),
                ('notify_count', models.IntegerField(default=0)),
                ('skipped', models.NullBooleanField(default=None)),
                ('call_type', models.CharField(default=b'm', max_length=2, choices=[(b'm', b'One Month'), (b'y', b'One Year')])),
                ('participant', models.ForeignKey(to='contacts.Contact')),
            ],
            options={
                'ordering': ('-scheduled',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StatusChange',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('old', models.CharField(max_length=20)),
                ('new', models.CharField(max_length=20)),
                ('type', models.CharField(default=b'status', max_length=10)),
                ('comment', models.TextField(blank=True)),
                ('contact', models.ForeignKey(to='contacts.Contact')),
            ],
        ),
        migrations.CreateModel(
            name='Visit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('scheduled', models.DateField()),
                ('arrived', models.DateField(default=None, null=True, blank=True)),
                ('notification_last_seen', models.DateField(default=None, null=True)),
                ('notify_count', models.IntegerField(default=0)),
                ('skipped', models.NullBooleanField(default=None)),
                ('comment', models.TextField(null=True, blank=True)),
                ('visit_type', models.CharField(default=b'clinic', max_length=25, choices=[(b'clinic', b'Clinic Visit'), (b'study', b'Study Visit')])),
                ('participant', models.ForeignKey(to='contacts.Contact')),
            ],
            options={
                'ordering': ('-scheduled',),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='phonecall',
            name='scheduled',
            field=models.ForeignKey(blank=True, to='contacts.ScheduledPhoneCall', null=True),
        ),
        migrations.AddField(
            model_name='connection',
            name='contact',
            field=models.ForeignKey(blank=True, to='contacts.Contact', null=True),
        ),
    ]
