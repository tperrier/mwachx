#!/usr/bin/python
 # -*- coding: utf-8 -*-
import datetime, openpyxl as xl, os
from argparse import Namespace
import code
import operator, collections, re, argparse

from django.core.management.base import BaseCommand, CommandError
from django.db import models

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
        send_time_parser.set_defaults(action='print_stats')

        xlsx_parser = subparsers.add_parser('xlsx',cmd=parser.cmd,help='create xlsx report')
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
        self.stdout.write( "Printing Stats: registered={} times={}".format(self.options['registered'],self.options['times']) )
        if self.options['registered']:
            self.registered_counts()
        if self.options['times']:
            self.send_times()
        if self.options['validation_codes']:
            self.validation_stats()

    def send_times(self):

        self.print_header("Participant Send Times")
        self.printed = True

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
        self.printed = True

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
        self.printed = True

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

    def print_header(self,header):
        if self.printed:
            self.stdout.write("")
        self.stdout.write( "-"*30 )
        self.stdout.write( "{:^30}".format(header) )
        self.stdout.write( "-"*30 )

    def make_xlsx(self):

        wb = xl.workbook.Workbook()
        ws = wb.active

        make_facility_sheet(ws,'ahero')
        make_facility_sheet(wb.create_sheet(),'bondo')
        make_facility_sheet(wb.create_sheet(),'mathare')

        today = datetime.date.today()
        xlsx_path_out = os.path.join(self.options['dir'],today.strftime('mWaChX_%Y-%m-%d.xlsx'))
        self.stdout.write( "Making xlsx file {}".format(xlsx_path_out) )
        wb.save(xlsx_path_out)

########################################
# Utility Functions
########################################

def make_facility_sheet(ws,facility):

    contacts = cont.Contact.objects.filter(facility=facility)
    ws.title = facility.capitalize()

    columns = collections.OrderedDict([
        ('Study ID','study_id'),
        ('Enrolled','created'),
        ('Group','study_group'),
        ('EDD','due_date'),
        ('Send Day','send_day'),
        ('Send Time','send_time'),
        ('Validation Δ',lambda c: seconds_as_str(c.validation_delta()) ),
        ('System', lambda c: c.message_set.filter(is_system=True).count() ),
        ('Nurse', lambda c: c.message_set.filter(is_system=False,is_outgoing=True).count() ),
        ('Client', lambda c: c.message_set.filter(is_outgoing=False).count() ),

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
