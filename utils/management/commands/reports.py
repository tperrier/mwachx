#!/usr/bin/python
 # -*- coding: utf-8 -*-
import datetime, openpyxl as xl, os
from argparse import Namespace
import code
import operator, collections, re, argparse

from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.utils import timezone

import utils.sms_utils as sms
import backend.models as back
import contacts.models as cont

class Command(BaseCommand):

    help = 'Parse and import SMS data bank'

    def add_arguments(self,parser):
        # code.interact(local=locals())
        subparsers = parser.add_subparsers(help='make reports')

        # The cmd argument is required for django.core.management.base.CommandParser
        send_time_parser = subparsers.add_parser('print',cmd=parser.cmd,help='report send time statistics')
        send_time_parser.add_argument('-t','--times',action='store_true',default=False,help='print send times')
        send_time_parser.add_argument('-r','--registered',action='store_true',default=False,help='print registered totals per facility')
        send_time_parser.add_argument('-c','--validation-codes',action='store_true',default=False,help='print validation stats')
        send_time_parser.add_argument('-m','--messages',action='store_true',default=False,help='print message statistics')
        send_time_parser.add_argument('-a','--all',action='store_true',default=False,help='all report options')
        send_time_parser.add_argument('--weeks',default=5,type=int,help='message history weeks (default 5)')
        send_time_parser.set_defaults(action='print_stats')

        xlsx_parser = subparsers.add_parser('xlsx',cmd=parser.cmd,help='create xlsx reports')
        xlsx_parser.add_argument('report_type',choices=('visit','detail','all'),help='name of report to make')
        xlsx_parser.add_argument('-d','--dir',default='ignore',help='directory to save report in')
        xlsx_parser.set_defaults(action='make_xlsx')

        custom_parser = subparsers.add_parser('custom',cmd=parser.cmd,help='run custom command')
        custom_parser.set_defaults(action='custom')

    def handle(self,*args,**options):

        self.stdout.write( 'Reports Action: {}'.format(options['action']) )

        self.printed = False
        self.options = options
        getattr(self,options['action'])()

    ########################################
    # Commands
    ########################################

    def print_stats(self):
        self.stdout.write( "Printing Stats: registered={0[registered]} times={0[times]} validation-codes={0[validation_codes]}".format(self.options) )
        if self.options['registered'] or self.options['all']:
            self.registered_counts()
        if self.options['times'] or self.options['all']:
            self.send_times()
        if self.options['validation_codes'] or self.options['all']:
            self.validation_stats()
        if self.options['messages'] or self.options['all']:
            self.message_stats()

    def send_times(self):

        self.print_header("Participant Send Times")

        c_all = cont.Contact.objects.all().order_by('send_day','send_time')
        time_counts = c_all.exclude(study_group='control').values('send_day','send_time') \
            .annotate(count=models.Count('send_day'))

        times, day , counts = {} ,0 , [0,0,0]
        day_lookup = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
        time_map = {8:0,13:1,20:2}
        for c in time_counts:
            if c['send_day'] == day:
                counts[time_map[c['send_time']]] = c['count']
            else:
                times[day] = counts
                day = c['send_day']
                counts = [0,0,0]
                counts[time_map[c['send_time']]] = c['count']
        times[day] = counts

        totals = [0,0,0]
        for i in range(7):
            t = times.get(i,[0,0,0])
            totals = [t1+t2 for t1,t2 in zip(totals,t)]
            self.stdout.write( "{} {} {}".format(day_lookup[i],t,sum(t)) )
        self.stdout.write( "Tot {} {}".format(totals,sum(totals)) )

    def registered_counts(self):

        self.print_header("Participant By Facility")

        c_all = cont.Contact.objects.all().order_by('study_group')
        group_counts = c_all.values('facility','study_group') \
            .annotate(count=models.Count('facility'))

        def CountRow():
            return {'control':0,'one-way':0,'two-way':0}
        counts = collections.defaultdict(CountRow)
        # Piviot Group Counts
        for g in group_counts:
            counts[g['facility']][g['study_group']] = g['count']

        self.stdout.write( "{:^12}{:^12}{:^12}{:^12}{:^12}".format("","Control","One-Way","Two-Way","Total") )
        total_row = CountRow()
        for facility, row in counts.items():
            self.stdout.write( "{:^12}{:^12}{:^12}{:^12}{:^12}".format(facility.capitalize(), row['control'], row['one-way'], row['two-way'],
                sum(row.values()) )
            )
            for group , count in row.items():
                total_row[group] += count

        self.stdout.write( "{:^12}{:^12}{:^12}{:^12}{:^12}".format("Total", total_row['control'], total_row['one-way'], total_row['two-way'],
            sum(total_row.values()) )
        )

    def validation_stats(self):

        self.print_header('Validation Stats')

        c_all = cont.Contact.objects.all()

        stats = collections.OrderedDict( ( ('< 1h',0) , ('< 1d',0) ,('> 1d',0) , ('None',0) ) )
        for c in c_all:
            seconds = c.validation_delta()
            if seconds is None:
                stats['None'] += 1
            elif seconds <= 3600:
                stats['< 1h'] += 1
            elif seconds <= 86400:
                stats['< 1d'] += 1
            elif seconds > 86400:
                stats['> 1d'] += 1
            else:
                stats['None'] += 1

        counts = dict( c_all.values_list('is_validated').annotate(count=models.Count('is_validated')) )

        total = sum(counts.values())
        self.stdout.write( "Total: {} Valididated: {} ({:0.3f}) Not-Validated: {} ({:0.3f})\n".format(
            total , counts[True] , counts[True] / float(total) , counts[False] , counts[False] / float(total)
        ) )

        for key , count in stats.items():
            self.stdout.write( "\t{}\t{} ({:0.3f})".format(key,count, count/float(total) ) )

    def message_stats(self):


        self.print_header('Message Statistics (system-participant-nurse)')

        # Get messages grouped by facility, system and outgoing
        m_all = cont.Message.objects.all()
        group_counts = m_all.order_by().values(
            'contact__facility','contact__study_group','is_system','is_outgoing'
        ).annotate(count=models.Count('contact__facility'))

        # Piviot Group Counts based on facility
        counts = collections.defaultdict(CountRow)
        for g in group_counts:
            facility = g['contact__facility']
            if facility is None:
                continue

            study_group = g['contact__study_group']
            sender = 'system'
            if not g['is_system']:
                sender = 'nurse' if g['is_outgoing'] else 'participant'
            counts[facility][study_group][sender] = g['count']

        # Print Message Totals Table
        self.stdout.write( "{:^10}{:^18}{:^18}{:^18}{:^18}".format("","Control","One-Way","Two-Way","Total") )
        total_row = CountRow()
        for facility , row in counts.items():
            total_row += row
            row['two-way'].replies = m_all.filter(parent__isnull=False,contact__facility=facility).count()
            self.stdout.write( '{:<10}{}  {} ({})'.format(facility,row,row.total(),sum(row.total()) ) )

        none_count = m_all.filter(contact__isnull=True).count()
        total_count = total_row.total()
        total_row['two-way'].replies = m_all.filter(parent__isnull=False).count()
        self.stdout.write( '{:<10}{}  {} ({})'.format('total',total_row,total_count,sum(total_count) ) )
        self.stdout.write( '{:<10}{:04d} ({})'.format('none',none_count,none_count+sum(total_count)) )

        # Print last 5 weeks of messaging
        self.stdout.write('')
        self.print_messages(self.options['weeks'])
    def print_messages(self,weeks=None):

        # Get all two-way messages
        m_all = cont.Message.objects.filter(contact__study_group='two-way')

        # Get start date
        study_start_date = timezone.make_aware(datetime.datetime(2015,11,23))
        now = timezone.now()
        weeks_start_date = timezone.make_aware(
            datetime.datetime(now.year,now.month,now.day) - datetime.timedelta(days=now.weekday())
        ) # Last Sunday
        start_date = study_start_date
        if weeks is not None and weeks_start_date > study_start_date:
            start_date = weeks_start_date - datetime.timedelta(days=weeks*7)

        total_row = CountRowItem()
        while start_date < now:
            end_date = start_date + datetime.timedelta(days=7)
            m_range = m_all.filter(created__range=(start_date,end_date))
            row = CountRowItem()
            row['system'] = m_range.filter(is_system=True).count()
            row['participant'] = m_range.filter(is_system=False,is_outgoing=False).count()
            row['nurse'] = m_range.filter(is_system=False,is_outgoing=True).count()
            row.replies = m_range.filter(parent__isnull=False).count()

            total_row += row
            self.stdout.write( '{}  {} ({})'.format(start_date.strftime('%Y-%m-%d'),row,sum(row) ) )
            start_date = end_date
        self.stdout.write( "Total       {} ({})".format(total_row,sum(total_row)) )


    def print_header(self,header):
        if self.printed:
            self.stdout.write("")
        self.printed = True

        self.stdout.write( "-"*30 )
        self.stdout.write( "{:^30}".format(header) )
        self.stdout.write( "-"*30 )

    def make_xlsx(self):

        wb = xl.workbook.Workbook()
        report_type = self.options['report_type']
        report_type_list = ['visit','detail'] if report_type == 'all' else [report_type]

        today = datetime.date.today()

        for report_type in report_type_list:
            file_name = today.strftime('mWaChX_{}_%Y-%m-%d.xlsx').format(report_type)
            xlsx_path_out = os.path.join(self.options['dir'],file_name)
            self.stdout.write( "Making xlsx file {}".format(xlsx_path_out) )

            ws_function = globals()['make_facility_{}_sheet'.format(report_type)]

            ws_function(wb.active,'ahero')
            ws_function(wb.create_sheet(),'bondo')
            ws_function(wb.create_sheet(),'mathare')

            wb.save(xlsx_path_out)

########################################
# Message Row Counting Classes
########################################

class CountRowItem(dict):

    columns = ['system','participant','nurse']

    def __init__(self):
        self.replies = 0
        for c in self.columns:
            self[c] = 0

    def __iter__(self):
        for v in self.values():
            yield v

    def __add__(self,other):
        new = CountRowItem()
        for c in self.columns:
            new[c] = self[c] + other[c]
        return new

    def __str__(self):
        reply_str = '' if not self.replies else '/{:04d}'.format(self.replies)
        return '{0[system]:04d}--{0[participant]:04d}{1}--{0[nurse]:04d}'.format(self,reply_str)

class CountRow(dict):

    columns = ['control','one-way','two-way']

    def __init__(self):
        for c in self.columns:
            self[c] = CountRowItem()

    def total(self):
        new = CountRowItem()
        for c in self.columns:
            new += self[c]
        return new

    def __add__(self,other):
        new = CountRow()
        for c in self.columns:
            new[c] = self[c] + other[c]
        return new

    def __str__(self):
        return '{0[control]}  {0[one-way]}  {0[two-way]}'.format(self)

########################################
# Utility Functions
########################################

def make_facility_detail_sheet(ws,facility):

    contacts = cont.Contact.objects.filter(facility=facility)
    ws.title = facility.capitalize()

    last_week = datetime.date.today() - datetime.timedelta(days=7)
    columns = collections.OrderedDict([
        ('Study ID','study_id'),
        ('Enrolled',lambda c: c.created.date()),
        ('Group','study_group'),
        ('EDD','due_date'),
        ('Δ EDD',lambda c:delta_days(c.due_date)),
        ('Delivery','delivery_date'),
        ('Δ Delivery',lambda c:delta_days(c.delivery_date,past=True)),
        ('TCA',lambda c:c.tca_date()),
        ('Validation Δ',lambda c: seconds_as_str(c.validation_delta()) ),
        ('Client', lambda c: c.message_set.filter(is_outgoing=False).count() ),
        ('Δ C', lambda c: c.message_set.filter(is_outgoing=False,created__gte=last_week).count() ),
        ('System', lambda c: c.message_set.filter(is_system=True).count() ),
        ('Δ S', lambda c: c.message_set.filter(is_system=True,created__gte=last_week).count() ),
        ('Nurse', lambda c: c.message_set.filter(is_system=False,is_outgoing=True).count() ),
        ('Δ N', lambda c: c.message_set.filter(is_system=False,is_outgoing=True,created__gte=last_week).count() ),
    ])

    # Write Header Row
    ws.append(columns.keys())
    ws.auto_filter.ref = 'A1:{}1'.format( xl.utils.get_column_letter(len(columns)) )

    column_widths = {'K':5,'M':5,'O':5}
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    # Write Data Rows
    for c in contacts:
        ws.append( [make_column(c,attr) for attr in columns.values()] )

def make_facility_visit_sheet(ws,facility):

    contacts = cont.Contact.objects.filter(facility=facility)
    ws.title = facility.capitalize()

    columns = collections.OrderedDict([
        ('Study ID','study_id'),
        ('Group','study_group'),
        ('Status','status'),
        ('EDD','due_date'),
        ('Δ EDD',lambda c:delta_days(c.due_date)),
        ('Delivery','delivery_date'),
        ('Δ Delivery',lambda c:delta_days(c.delivery_date,past=True)),
        ('TCA',lambda c:c.tca_date()),
        ('Δ TCA',lambda c:delta_days(c.tca_date())),
        ('Pending Visits',lambda c:c.visit_set.pending().count()),
    ])

    # Write Header Row
    ws.append(columns.keys())
    ws.auto_filter.ref = 'A1:{}1'.format( xl.utils.get_column_letter(len(columns)) )

    column_widths = {'B':20,'C':15, }
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    # Write Data Rows
    for c in contacts:
        ws.append( [make_column(c,attr) for attr in columns.values()] )

def make_column(obj,column):
    if isinstance(column,basestring):
        value = getattr(obj,column)
        if hasattr(value,'__call__'):
            return value()
        return value
    # Else assume column is a function that takes the object
    return column(obj)

def seconds_as_str(seconds):
    if seconds is None:
        return None
    if seconds <= 3600:
        return '{:.2f}'.format(seconds/60)
    return '{:.2f} (h)'.format(seconds/3600)

def delta_days(date,past=False):
    if date is not None:
        days = (date - datetime.date.today()).days
        return -days if past else days
