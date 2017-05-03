#!/usr/bin/python
 # -*- coding: utf-8 -*-
import datetime, openpyxl as xl, os
from argparse import Namespace
import operator, collections, re, argparse, csv, code

from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.utils import timezone , dateparse

import backend.models as back
import contacts.models as cont

class Command(BaseCommand):

    help = 'Create message reports xlsx sheets'

    def add_arguments(self,parser):
        # code.interact(local=locals())
        parser.add_argument('--dir',default='ignore',help='directory to save report in')
        subparsers = parser.add_subparsers(help='make reports')

        # The cmd argument is required for django.core.management.base.CommandParser
        message_parser = subparsers.add_parser('msgs',cmd=parser.cmd,help='report messages from one-way,control, and anonymous numbers')
        message_parser.add_argument('-g','--study-group',default='all',choices=('anonymous','one-way','control','all'),help='study group to select')
        message_parser.add_argument('-s','--start',default=None,help='date to start from (one week ago)')
        message_parser.add_argument('-e','--end',default=None,help='date to end from (now)')
        message_parser.add_argument('-a','--all',default=False,action='store_true',help='ignore time filters all messages')
        message_parser.add_argument('-w','--weeks',default=2,type=int,help='number of weeks if start and end are None')
        message_parser.set_defaults(action='make_messages')

        weekly_parser = subparsers.add_parser('weekly',cmd=parser.cmd,help='report weekly message counts and status by group, sender')
        weekly_parser.add_argument('-f','--file',default='weekly_messages.xlsx',help='file name (weekly_messages.xlsx)')
        weekly_parser.add_argument('-t','--totals',default=False,action='store_true',help='only show totals')
        weekly_parser.add_argument('-w','--weeks',default=1,type=int,help='number of weeks if start and end are None')
        weekly_parser.add_argument('-s','--start',default=None,help='date to start from (one week ago)')
        weekly_parser.add_argument('-e','--end',default=None,help='date to end from (now)')
        weekly_parser.add_argument('-a','--all',default=False,action='store_true',help='ignore time filters all messages')
        weekly_parser.set_defaults(action='make_weekly')

    def handle(self,*args,**options):

        self.stdout.write( 'Reports Action: {}'.format(options['action']) )

        self.options = options
        getattr(self,options['action'])()

    ########################################
    # Commands
    ########################################

    def make_messages(self):

        wb = xl.Workbook()
        ws = wb.active
        if self.options['study_group'] == 'one-way':
            ws.title = 'one-way'
            self.make_message_ws(ws,'one-way')
        elif self.options['study_group'] == 'control':
            ws.title = 'control'
            self.make_message_ws(ws,'control')
        elif self.options['study_group'] == 'anonymous':
            ws.title = 'anonymous'
            self.make_message_ws(ws,'anonymous')
        elif self.options['study_group'] == 'all':
            ws.title = 'one-way'
            self.make_message_ws(ws,'one-way')
            ws = wb.create_sheet('control')
            self.make_message_ws(ws,'control')
            ws = wb.create_sheet('anonymous')
            self.make_message_ws(ws,'anonymous')
        wb.save('ignore/{}_messages.xlsx'.format(self.options['study_group']))

    def make_message_ws(self,ws,study_group='one-way'):

        # get a default message set with no time filters
        if study_group == 'anonymous':
            messages = cont.Message.objects.filter(contact__isnull=True)
        else:
            messages = cont.Message.objects.filter(
                contact__study_group=study_group,
                is_outgoing=False
            ).exclude(
                topic='validation'
            )

        start , end = "begining" , "end"

        # Filter messages based on start and end
        if self.options['all'] is False:
            start = datetime.date.today() - datetime.timedelta(weeks=self.options['weeks'])
            if self.options['start'] is not None:
                start = dateparse.parse_date(self.options['start'])
            end = datetime.date.today()
            if self.options['end'] is not None:
                end = dateparse.parse_date(self.options['end'])
            start , end = to_datetime(start) , to_datetime(end)
            messages = messages.filter(created__range=(start,end))

        self.stdout.write( 'Creating Report: {}'.format(study_group) )
        self.stdout.write( 'Found {} messages from {} to {}'.format(messages.count(),start,end))

        if study_group != 'anonymous':
            ws.append( ("Study ID","Message","Date","Previous","Date","Type","Delta") )
            for msg in messages:
                ws.append( (
                    msg.contact.study_id,
                    msg.translated_text if msg.translated_text != '' else msg.text,
                    msg.created,
                    msg.previous_outgoing.text,
                    msg.previous_outgoing.created,
                    msg.previous_outgoing.auto if msg.previous_outgoing.is_system else msg.previous_outgoing.sent_by(),
                    delta_str(msg.previous_outgoing.created,msg.created),
                ) )
                ws.cell(row=ws.max_row,column=2).alignment = xl.styles.Alignment(wrap_text=True)
                ws.cell(row=ws.max_row,column=4).alignment = xl.styles.Alignment(wrap_text=True)
            ws.column_dimensions['B'].width = 40
            ws.column_dimensions['C'].width = 20
            ws.column_dimensions['D'].width = 40
            ws.column_dimensions['E'].width = 20
            ws.column_dimensions['F'].width = 20
        else:
            ws.append( ("Phone Number","Message","Date") )
            for msg in messages:
                ws.append( (
                    msg.connection.identity,
                    msg.text,
                    msg.created,
                ) )
                ws.cell(row=ws.max_row,column=2).alignment = xl.styles.Alignment(wrap_text=True)
            ws.column_dimensions['A'].width = 20
            ws.column_dimensions['B'].width = 40
            ws.column_dimensions['C'].width = 20

    def make_weekly(self):

        start = datetime.date.today() - datetime.timedelta(weeks=self.options['weeks'])
        if self.options['start'] is not None:
            start =  dateparse.parse_date(self.options['start'])
        if self.options['all'] is True:
            start = dateparse.parse_date("2015-11-01")

        end = datetime.date.today() + datetime.timedelta(days=2)
        if self.options['end'] is not None:
            end = dateparse.parse_date(self.options['end'])

        start , end = to_datetime(start) , to_datetime(end)
        messages = cont.Message.objects.filter(contact__isnull=False,created__range=(start,end))

        self.stdout.write( 'Creating One Way Report: {}'.format(self.file_name) )
        self.stdout.write( 'Found {} messages from {} to {}'.format(messages.count(),start,end))

        wb = xl.Workbook()
        ws = wb.active
        ws.title = 'weekly'
        ws.append( ("Date","Two-Way","One-Way","Control","Validation",
            "Nurse",
                "Sent","Missed","Failed",
            "System",
                "Sent","Missed","Failed",
            "Visit",
                "Sent","Missed","Failed",
            "Signup",
                "Sent","Missed","Failed",
            "Outgoing",
                "Sent","Missed","Failed",
            "Total" ) )
        total_row =  collections.OrderedDict(
            [("two-way",0),("one-way",0),("control",0),("validation",0),
            ("nurse",0),
                ("nS",0),("nM",0),("nF",0),
            ("system",0),
                ("sS",0),("sM",0),("sF",0),
            ("visit",0),
                ("vS",0),("vM",0),("vF",0),
            ("signup",0),
                ("eS",0),("eM",0),("eF",0),
            ("outgoing",0),
                ("oS",0),("oM",0),("oF",0),
            ("total",0)]
        )
        for day in days_itr(start,end):
            next_day = day + datetime.timedelta(days=1)
            day_messages = messages.filter(created__range=(day,next_day))
            row = make_message_row(day_messages)
            total = sum(row.values())
            row["total"] = total
            ws.append( [day.date()] + row.values() )
            for key , value in row.items():
                total_row[key] += value
        ws.append( ["Total"] + total_row.values() )
        print '\n'.join( str(i) for i in total_row.items() )
        wb.save(self.file_name)

    ########################################
    #  Class Utility Functions
    ########################################
    @property
    def file_name(self):
        return os.path.join(self.options['dir'],self.options['file'])

########################################
# Global Utility Functions
########################################

def make_message_row(messages):
    row = collections.OrderedDict(
        [("two-way",0),("one-way",0),("control",0),("validation",0),
        ("nurse",0),
            ("nS",0),("nM",0),("nF",0),
        ("system",0),
            ("sS",0),("sM",0),("sF",0),
        ("visit",0),
            ("vS",0),("vM",0),("vF",0),
        ("signup",0),
            ("eS",0),("eM",0),("eF",0),
        ("outgoing",0),
            ("oS",0),("oM",0),("oF",0),
        ("total",0)]
    )
    for msg in messages:
        prefix_char = 'n'
        if msg.is_outgoing:
            if msg.is_system:
                send_base = msg.auto.split('.')[0]
                if send_base in ('visit','signup'):
                    row[send_base] += 1
                    prefix_char = 'v' if send_base == 'visit' else 'e'
                else:
                    row['system'] += 1
                    prefix_char = 's'
            else: # not system
                row['nurse'] += 1
            row['outgoing'] += 1
            row['o' + get_suffex_char(msg)] += 1
            row[prefix_char + get_suffex_char(msg)] += 1
        else: # not outgoing
            if msg.topic == 'validation':
                row['validation'] += 1
            else:
                row[msg.contact.study_group] += 1
    return row

def get_suffex_char(msg):
    if msg.external_status == "Success":
        return "S"
    elif msg.external_status == "Sent":
        return "M"
    else:
        return "F"

def delta_str(start,end=None):
    if end is None:
        end = datetime.datimetime.now()
    start = to_datetime(start)
    end = to_datetime(end)
    delta_seconds = (end - start).total_seconds()
    days , delta_seconds = divmod(delta_seconds,86400)
    hours , delta_seconds = divmod(delta_seconds,3600)
    minutes , seconds = divmod(delta_seconds,60)

    output = "%im" % minutes
    if hours:
        output = "%ih %s" % (hours,output)
    if days:
        output = "%id %s" % (days,output)
    return output


def to_datetime(d):
    return timezone.make_aware(datetime.datetime(*d.timetuple()[:6]))

def days_itr(start,end=None):
    if end is None:
        end = datetime.date.today()
    while start < end:
        yield start
        start += datetime.timedelta(days=1)
