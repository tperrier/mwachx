#!/usr/bin/python
 # -*- coding: utf-8 -*-
import datetime, openpyxl as xl, os
from argparse import Namespace
import code
import operator, collections, re, argparse, csv

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
        print_parser = subparsers.add_parser('print',cmd=parser.cmd,help='report send time statistics')
        print_parser.add_argument('-t','--times',action='store_true',default=False,help='print send times')
        print_parser.add_argument('-f','--facilities',action='store_true',default=False,help='print registered totals per facility')
        print_parser.add_argument('-c','--validation-codes',action='store_true',default=False,help='print validation stats')
        print_parser.add_argument('-m','--messages',action='store_true',default=False,help='print message statistics')
        print_parser.add_argument('-a','--all',action='store_true',default=False,help='all report options')
        print_parser.add_argument('-o','--hours',action='store_true',default=False,help='print hist of message hours')
        print_parser.add_argument('-i','--hiv',action='store_true',default=False,help='print hiv messaging status')
        print_parser.add_argument('-l','--language',action='store_true',default=False,help='print language histogram')
        print_parser.add_argument('-s','--status',action='store_true',default=False,help='print status histogram')
        print_parser.add_argument('-e','--enrollment',action='store_true',default=False,help='print enrollment by site')
        print_parser.add_argument('-d','--delivery',action='store_true',default=False,help='print delivery statistics')
        print_parser.add_argument('--delivery-source',action='store_true',default=False,help='print delivery source statistics')
        print_parser.add_argument('--weeks',default=5,type=int,help='message history weeks (default 5)')
        print_parser.set_defaults(action='print_stats')

        xlsx_parser = subparsers.add_parser('xlsx',cmd=parser.cmd,help='create xlsx reports')
        xlsx_parser.add_argument('-t','--visit',action='store_true',default=False,help='create visit report')
        xlsx_parser.add_argument('-d','--detail',action='store_true',default=False,help='create detail report')
        xlsx_parser.add_argument('-a','--all',action='store_true',default=False,help='create all reports')
        xlsx_parser.add_argument('-c','--custom',action='store_true',default=False,help='create custom report')
        xlsx_parser.add_argument('--dir',default='ignore',help='directory to save report in')
        xlsx_parser.set_defaults(action='make_xlsx')

        csv_parser = subparsers.add_parser('csv',cmd=parser.cmd,help='create csv reports')
        csv_parser.add_argument('--dir',default='ignore',help='directory to save csv in')
        csv_parser.set_defaults(action='make_csv')

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

        if self.options['facilities'] or self.options['all']:
            self.participants_by_facility()
        if self.options['times'] or self.options['all']:
            self.send_times()
        if self.options['status'] or self.options['all']:
            self.status_breakdown()
        if self.options['validation_codes'] or self.options['all']:
            self.validation_stats()
        if self.options['messages'] or self.options['all']:
            self.message_stats()
        if self.options['hiv'] or self.options['all']:
            self.hiv_messaging()
        if self.options['hours']:
            self.message_hours()
        if self.options['language']:
            self.print_languages()
        if self.options['enrollment']:
            self.print_enrollment()
        if self.options['delivery']:
            self.print_delivery_stats()
        if self.options['delivery_source'] and not self.options['delivery']:
            self.print_delivery_source()

    def send_times(self):

        self.print_header("Participant Send Times")

        c_all = cont.Contact.objects_no_link.all().order_by('send_day','send_time')
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

    def participants_by_facility(self):

        self.print_header("Participant By Facility")

        group_counts = cont.Contact.objects.values('facility','study_group') \
            .annotate(count=models.Count('study_id',distinct=True))

        # Piviot Group Counts
        counts = collections.defaultdict(GroupRowCount)

        for g in group_counts:
            counts[g['facility']][g['study_group']] = g['count']

        # Print Group Counts
        self.stdout.write( "{:^12}{:^12}{:^12}{:^12}{:^12}".format("","Control","One-Way","Two-Way","Total") )
        total_row = GroupRowCount()
        for facility, row in counts.items():
            self.stdout.write( "{:^12}{:^12}{:^12}{:^12}{:^12}".format(
                facility.capitalize(), row['control'], row['one-way'], row['two-way'], row.total())
            )
            total_row += row

        self.stdout.write( "{:^12}{:^12}{:^12}{:^12}{:^12}".format(
            "Total", total_row['control'], total_row['one-way'], total_row['two-way'], total_row.total() )
        )

    def validation_stats(self):

        self.print_header('Validation Stats')

        c_all = cont.Contact.objects_no_link.all()

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
        counts = collections.defaultdict(MessageRow)
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
        total_row = MessageRow()
        for facility , row in counts.items():
            total_row += row
            row['two-way'].replies = m_all.filter(parent__isnull=False,contact__facility=facility).count()
            self.stdout.write( '{:<10}{}  {} ({})'.format(facility.capitalize(),row,row.total(),row.total().total() ) )

        none_count = m_all.filter(contact__isnull=True).count()
        total_count = total_row.total()
        total_row['two-way'].replies = m_all.filter(parent__isnull=False).count()
        self.stdout.write( '{:<10}{}  {} ({})'.format('Total',total_row,total_count,sum(total_count) ) )
        self.stdout.write( '{:<10}{:04d} ({})'.format('None',none_count,none_count+sum(total_count)) )

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

        total_row = MessageRowItem()
        while start_date < now:
            end_date = start_date + datetime.timedelta(days=7)
            m_range = m_all.filter(created__range=(start_date,end_date))
            row = MessageRowItem()
            row['system'] = m_range.filter(is_system=True).count()
            row['participant'] = m_range.filter(is_system=False,is_outgoing=False).count()
            row['nurse'] = m_range.filter(is_system=False,is_outgoing=True).count()
            row.replies = m_range.filter(parent__isnull=False).count()

            total_row += row
            self.stdout.write( '{}  {} ({})'.format(start_date.strftime('%Y-%m-%d'),row,sum(row) ) )
            start_date = end_date
        self.stdout.write( "Total       {} ({})".format(total_row,sum(total_row)) )

    def message_hours(self):

        self.print_header('Histogram of message send hour (two-way only)')

        messages , hour_counts = {} , {}
        messages['p'] = cont.Message.objects.filter(is_outgoing=False,contact__study_group='two-way')
        messages['s'] = cont.Message.objects.filter(is_outgoing=True,is_system=True,contact__study_group='two-way')
        messages['n'] = cont.Message.objects.filter(is_outgoing=True,is_system=False,contact__study_group='two-way')

        for k in messages.keys():
            hours = [0 for _ in range(24)]
            for m in messages[k]:
                hours[m.created.hour] += 1
            hour_counts[k] = hours

        print "     C    S    N"
        for h in range(24):
            print "{0:<5}{1:<5}{2:<5}{3:<5}".format((h+3)%24,hour_counts['p'][h],hour_counts['s'][h],hour_counts['n'][h])
        print "     {0:<5}{1:<5}{2:<5}".format(*map(sum,[hour_counts[k] for k in ('p','s','n')]))

    def hiv_messaging(self):

        self.print_header('HIV Messaging Preference (none-initiated-system)')

        hiv_messaging_groups = cont.Contact.objects.order_by().values('facility','study_group','hiv_messaging') \
            .annotate(count=models.Count('study_id',distinct=True))

        # Piviot Group Counts
        group_counts = collections.defaultdict(HivRowCount)

        for g in hiv_messaging_groups:
            group_counts[g['facility']][g['study_group']][g['hiv_messaging']] = g['count']

        # Print Group Counts
        self.stdout.write( "{:^12}{:^12}{:^12}{:^12}{:^12}".format("","Control","One-Way","Two-Way","Total") )
        total_row = HivRowCount()
        for facility, row in group_counts.items():
            self.stdout.write( "{0:^12}{1[control]:^12}{1[one-way]:^12}{1[two-way]:^12}{2:^12}".format(
                facility.capitalize(), row, row.total()
            ) )
            total_row += row

        self.stdout.write( "{0:^12}{1[control]:^12}{1[one-way]:^12}{1[two-way]:^12} {2:^12}".format(
            "Total", total_row, total_row.total()
        ) )

    def print_languages(self):

        self.print_header('Language Statistics (english,swahili,luo)')

        language_groups = cont.Contact.objects.order_by().values('facility','study_group','language') \
            .annotate(count=models.Count('study_id',distinct=True))


        # Piviot Group Counts
        language_counts = collections.defaultdict(LanguageRow)
        for g in language_groups:
            language_counts[g['facility']][g['study_group']][g['language']] = g['count']

        # Print Group Counts
        self.stdout.write( "{:^12}{:^12}{:^12}{:^12}{:^12}".format("","Control","One-Way","Two-Way","Total") )
        total_row = LanguageRow()
        for facility, row in language_counts.items():
            self.stdout.write( "{0:^12}{1[control]:^12}{1[one-way]:^12}{1[two-way]:^12}{2:^12}".format(
                facility.capitalize(), row, row.total()
            ) )
            total_row += row

        self.stdout.write( "{0:^12}{1[control]:^12}{1[one-way]:^12}{1[two-way]:^12} {2:^12}".format(
            "Total", total_row, total_row.total()
        ) )

        print ''
        self.print_header('Language of Messages (participant,nurse)')

        message_groups = cont.Message.objects.order_by().filter(contact__study_group='two-way',is_system=False)\
            .prefetch_related('contact').values('languages','contact__language','is_outgoing')\
            .exclude(languages='').annotate(count=models.Count('id',distinct=True))

        # Piviot Group Counts
        language_counts = collections.defaultdict(LanguageMessageRow)
        for g in message_groups:
            language_counts[g['languages']][g['contact__language']][g['is_outgoing']] = g['count']

        # Print Group Counts
        self.stdout.write( "{:^12}{:^12}{:^12}{:^12}{:^12}".format("","English","Swahili","Luo","Total") )
        total_row = LanguageMessageRow()
        for language, row in language_counts.items():
            self.stdout.write( "{0:^12}{1[english]:^12}{1[swahili]:^12}{1[luo]:^12}{2:^12}".format(
                ','.join(s[0] for s in language.split(';')), row, row.total()
            ) )
            total_row += row

        self.stdout.write( "{0:^12}{1[english]:^12}{1[swahili]:^12}{1[luo]:^12}{2:^12}".format(
            "Total", total_row, total_row.total()
        ) )

    def status_breakdown(self):

        self.print_header('Participant Status (control,one-way,two-way)')

        status_groups = cont.Contact.objects.order_by().values('facility','status','study_group')\
            .annotate(count=models.Count('study_id',distinct=True))

        # Piviot Group Counts
        status_counts = collections.defaultdict(StatusRow)
        for g in status_groups:
            status_counts[g['facility']][g['status']][g['study_group']] = g['count']

        # Print Group Counts
        self.stdout.write( StatusRow.header() )
        total_row = StatusRow()
        for facility, row in status_counts.items():
            self.stdout.write( row.row_str(facility) )
            total_row += row

        self.stdout.write( total_row.row_str("Total") )

    def print_delivery_stats(self):

        self.print_header('Participant Delivery Stats')

        today = datetime.date.today()
        c_all = cont.Contact.objects.all()
        edd = c_all.filter(status='pregnant').order_by('due_date')
        post = edd.filter(due_date__lt=today)
        self.stdout.write( 'Found {:d} pregnant participants with {:d} post edd'.format(
            edd.count(), post.count()
        ) )

        future_edd = edd.order_by("-due_date")
        self.stdout.write( 'Furthest from EDD')
        for p in future_edd[:5]:
            self.stdout.write( "\t{0.study_id} {0.due_date} {0.study_group} (weeks {1:.0f})".format(
                p, p.delta_days() / 7
            ) )
        self.stdout.write( '\n')
        # self.stdout.write( 'Furthest EDD for #{:s} on {:s} ({:.0f} weeks)'.format(
        #     future_edd.study_id, future_edd.due_date.isoformat(), (today - future_edd.due_date).total_seconds()/604800
        # ) )

        self.stdout.write( 'Furthest past EDD')
        for p in edd[:5]:
            self.stdout.write( "\t{0.study_id} {0.due_date} {0.study_group} (weeks {1:.0f})".format(
                p, p.delta_days() / 7
            ) )
        self.stdout.write( '\n')

        dd = c_all.filter(delivery_date__isnull=False).order_by('delivery_date')
        self.stdout.write( 'Found {:d} post-partum participants'.format(dd.count()) )
        self.stdout.write( 'Furthest from delivery date')
        for p in dd[:5]:
            self.stdout.write( "\t{0.study_id} {0.due_date} {0.delivery_date}  {0.study_group} (weeks {1:.0f})".format(
                p, p.delta_days() / 7
            ) )
        self.stdout.write( '\n')

        # Add edd to dd delta seconds
        dd_min , dd_max , dd_total , dd_count = None , None , 0 , dd.count()
        dd_hist = [0 for _ in range(-10,11)]
        for p in dd:
            p.delivery_delta = (p.delivery_date - p.due_date).total_seconds()
            if dd_min is None or dd_min.delivery_delta > p.delivery_delta:
                dd_min = p
            if dd_max is None or dd_max.delivery_delta < p.delivery_delta:
                dd_max = p
            dd_total += p.delivery_delta
            dd_weeks = int(p.delivery_delta / 604800) + 10
            if dd_weeks < 0:
                dd_weeks = 0
            elif dd_weeks > 20:
                dd_weeks = 20
            dd_hist[dd_weeks] += 1

        self.stdout.write( 'Min {:s} (weeks {:.0f})  Max: {:s} (weeks {:.0f}) Average: {:f}'.format(
            dd_min.study_id , dd_min.delivery_delta/604800 ,
            dd_max.study_id , dd_max.delivery_delta/604800,
            dd_total/(dd_count*604800)
        ) )

        table = ""
        for c in range(-10,11):
            table += ' {:2.0f} '.format(c)
        table += '\n' + '----'*21 + '\n'
        for c in dd_hist:
            table += ' {:2.0f} '.format(c)
        self.stdout.write(table)

        self.print_delivery_source()

    def print_delivery_source(self):

        self.print_header('Participant Delivery Source (control,one-way,two-way)')

        source_groups = cont.Contact.objects_no_link.filter(delivery_date__isnull=False).order_by().values('facility',\
            'study_group','delivery_source').annotate(count=models.Count('delivery_source'))

        # for g in source_groups:
        #     print g
        # return

        # Piviot Group Counts
        source_counts = collections.defaultdict(DeliverySourceItem)
        for g in source_groups:
            source_counts[g['facility']][g['delivery_source']][g['study_group']] = g['count']

        # Print Group Counts
        self.stdout.write( DeliverySourceItem.header() )
        total_row = DeliverySourceItem()
        for facility, row in source_counts.items():
            self.stdout.write( row.row_str(facility) )
            total_row += row

        self.stdout.write( total_row.row_str("Total") )

    def print_enrollment(self):

        self.print_header('Participant Enrollment By Week')

        c_all = cont.Contact.objects.all()

        enrollment_counts = collections.OrderedDict()

        for c in c_all:
            key = c.created.strftime('%Y-%U')
            try:
                enrollment_counts[key][c.facility] += 1
            except KeyError as e:
                enrollment_counts[key] = FacilityRow()
                enrollment_counts[key][c.facility] += 1


        self.stdout.write( "{:^12}{:^12}{:^12}{:^12}{:^12}{:^12}{:^12}{:^12}".format(
            "Week","Ahero","Bondo","Mathare","Siaya","Rachuonyo","Riruta","Total") )
        total_row = FacilityRow()
        for week , enrollment in enrollment_counts.items():
            print week, enrollment, enrollment.total()
            total_row += enrollment
        print 'Total  ' , total_row , total_row.total()

    def print_header(self,header):
        if self.printed:
            self.stdout.write("")
        self.printed = True

        self.stdout.write( "-"*30 )
        self.stdout.write( "{:^30}".format(header) )
        self.stdout.write( "-"*30 )

    def make_xlsx(self):

        workbook_columns = {}
        if self.options['visit'] or self.options['all']:
            workbook_columns['visit'] =  visit_columns
        if self.options['detail'] or self.options['all']:
            workbook_columns['detail'] =  detail_columns
        if self.options['custom']:
            workbook_columns['custom'] =  detail_columns

        for name , columns in workbook_columns.items():

            wb = xl.workbook.Workbook()
            today = datetime.date.today()
            file_name = today.strftime('mWaChX_{}_%Y-%m-%d.xlsx').format(name)
            xlsx_path_out = os.path.join(self.options['dir'],file_name)
            self.stdout.write( "Making xlsx file {}".format(xlsx_path_out) )

            make_worksheet(columns,wb.active,'ahero')
            make_worksheet(columns,wb.create_sheet(),'bondo')
            make_worksheet(columns,wb.create_sheet(),'mathare')
            make_worksheet(columns,wb.create_sheet(),'siaya')
            make_worksheet(columns,wb.create_sheet(),'rachuonyo')
            make_worksheet(columns,wb.create_sheet(),'riruta')

            wb.save(xlsx_path_out)

    def make_csv(self):
        ''' Quick CSV of hiv messaging '''

        hiv_disclosed_values = {True:1,False:0,None:99}
        columns = collections.OrderedDict([
            ('study_id','study_id'),
            ('hiv_messaging','hiv_messaging'),
            ('hiv_disclosed', null_boolean_factory('hiv_disclosed')),
            ('phone_shared', null_boolean_factory('phone_shared')),
        ])

        contacts = cont.Contact.objects.all().order_by('study_id')
        csv_file_path = os.path.join(self.options['dir'],'mx_data_dump.csv')
        with open( csv_file_path , 'wb') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Header Row
            csv_writer.writerow( columns.keys() )

            for c in contacts:
                csv_writer.writerow( [ make_column(c,value) for value in columns.values()] )


########################################
# XLSX Helper Functions
########################################


last_week = datetime.date.today() - datetime.timedelta(days=7)
detail_columns = collections.OrderedDict([
    ('Study ID','study_id'),
    ('Enrolled',lambda c: c.created.date()),
    ('Group','study_group'),
    ('HIV','hiv_messaging') ,
    ('Disclosed','hiv_disclosed') ,
    ('Shared','phone_shared') ,
    ('EDD','due_date'),
    ('Δ EDD',lambda c:delta_days(c.due_date)),
    ('Delivery','delivery_date'),
    ('CCC Num','ccc_num'),
    ('ANC Num','anc_num'),
    ('Δ Delivery',lambda c:delta_days(c.delivery_date,past=True)),
    ('Client', lambda c: c.message_set.filter(is_outgoing=False).count() ),
    ('Δ C', lambda c: c.message_set.filter(is_outgoing=False,created__gte=last_week).count() ),
    ('System', lambda c: c.message_set.filter(is_system=True).count() ),
    ('Δ S', lambda c: c.message_set.filter(is_system=True,created__gte=last_week).count() ),
    ('Nurse', lambda c: c.message_set.filter(is_system=False,is_outgoing=True).count() ),
    ('Δ N', lambda c: c.message_set.filter(is_system=False,is_outgoing=True,created__gte=last_week).count() ),
    ('Validation Δ',lambda c: seconds_as_str(c.validation_delta()) ),
])

visit_columns = collections.OrderedDict([
    ('Study ID','study_id'),
    ('Group','study_group'),
    ('Status','status'),
    ('EDD','due_date'),
    ('Δ EDD',lambda c:delta_days(c.due_date)),
    ('Delivery','delivery_date'),
    ('Δ Delivery',lambda c:delta_days(c.delivery_date,past=True)),
    ('TCA',lambda c:c.tca_date()),
    ('Δ TCA',lambda c:delta_days(c.tca_date())),
    ('TCA Type',lambda c:c.tca_type()),
    ('Pending Visits',lambda c:c.visit_set.pending().count()),
])


def make_worksheet(columns,ws,facility,column_widths=None):
    contacts = cont.Contact.objects.filter(facility=facility)
    ws.title = facility.capitalize()

    # Write Header Row
    ws.append(columns.keys())
    ws.auto_filter.ref = 'A1:{}1'.format( xl.utils.get_column_letter(len(columns)) )

    if isinstance(column_widths,dict):
        for col_letter, width in column_widths.items():
            ws.column_dimensions[col_letter].width = width

    # Write Data Rows
    for c in contacts:
        ws.append( [make_column(c,attr) for attr in columns.values()] )

def null_boolean_factory(attribute):

    def null_boolean(obj):
        value = getattr(obj,attribute)
        if value is None:
            return 99
        if value is True:
            return 1
        return 0

    return null_boolean

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

########################################
# Message Row Counting Classes
########################################

class CountRowBase(dict):

    columns = " DEFINE COLUMN LIST IN SUBCLASS "
    child_class = int

    def __init__(self):
        for c in self.columns:
            self[c] = self.child_class()

    def __add__(self,other):
        new = self.__class__()
        for c in self.columns:
            new[c] = self[c] + other[c]
        return new

    def __iadd__(self,other):
        for c in self.columns:
            self[c] += other[c]
        return self

    def __iter__(self):
        """ Iterate over values instead of keys """
        for v in self.values():
            yield v

    def total(self):
        new = self.child_class()
        for c in self.columns:
            new += self[c]
        return new

    def __str__(self):
        return '  '.join( str(self[c]) for c in self.columns )

class MessageRowItem(CountRowBase):

    columns = ['system','participant','nurse']

    def __init__(self):
        self.replies = 0
        for c in self.columns:
            self[c] = 0

    def __str__(self):
        reply_str = '' if not self.replies else '/{:04d}'.format(self.replies)
        return '{0[system]:04d}--{0[participant]:04d}{1}--{0[nurse]:04d}'.format(self,reply_str)

class MessageRow(CountRowBase):
    columns = ['control','one-way','two-way']
    child_class = MessageRowItem

class GroupRowCount(CountRowBase):
    columns = ['control','one-way','two-way']

    @property
    def condensed(self):
        return self.condensed_str()

    def condensed_str(self):
        row =  '--'.join( '{:02d}'.format(self[c]) for c in self.columns )
        return "{} ({:03d})".format(row,sum(self.values()))

class HivRowItem(CountRowBase):
    columns = ['none','initiated','system']

    def __str__(self):
        return '--'.join( '{:02d}'.format(self[c]) for c in self.columns )

class HivRowCount(CountRowBase):
    columns = ['control','one-way','two-way']
    child_class = HivRowItem

class LanguageRowItem(CountRowBase):
    columns = ['english','swahili','luo']

    def __str__(self):
        return '--'.join( '{:02d}'.format(self[c]) for c in self.columns )

class LanguageRow(CountRowBase):
    columns = ['control','one-way','two-way']
    child_class = LanguageRowItem

class FacilityRow(CountRowBase):
    columns = ['ahero','bondo','mathare','siaya','rachuonyo','riruta']

    def __str__(self):
        return '   ' + ''.join( '{:^12}'.format(self[c]) for c in self.columns )

class LanguageMessageRowItem(CountRowBase):
    # Is Ougtgoing
    columns = [False,True]

    def __str__(self):
        return '--'.join( '{:02d}'.format(self[c]) for c in self.columns )

class LanguageMessageRow(CountRowBase):
    columns = ['english','swahili','luo']
    child_class = LanguageMessageRowItem

class StatusRow(CountRowBase):
    columns = ['pregnant','post','loss','sae','other','stopped']
    child_class = GroupRowCount

    @classmethod
    def header(cls):
        return "{:^12}{:^18}{:^18}{:^18}{:^18}{:^18}{:^18}".format(
            "","Pregnant","Post-Partum","SAE OptIn","SAE OptOut","Withdrew","Total"
        )

    def row_str(self,label):
        str_fmt = "{0:^12}{1[pregnant].condensed:^18}{1[post].condensed:^18}{1[loss].condensed:^18}"
        str_fmt += "{1[sae].condensed:^18}{1[stopped].condensed:^18}{2:^18}"
        return str_fmt.format( label , self, self.total().condensed_str() )

class DeliverySourceItem(CountRowBase):
    columns = ['phone','sms','visit','m2m','other','']
    child_class = GroupRowCount

    @classmethod
    def header(cls):
        return "{:^12}{:^18}{:^18}{:^18}{:^18}{:^18}{:^18}{:^18}".format(
            "","Phone","SMS","Clinic Visit","Mothers to Mothers","Other","None","Total"
        )

    def row_str(self,label):
        str_fmt = "{0:^12}{1[phone].condensed:^18}{1[sms].condensed:^18}{1[visit].condensed:^18}"
        str_fmt += "{1[m2m].condensed:^18}{1[other].condensed:^18}{2:^18}{3:^18}"
        return  str_fmt.format( label, self, self[''].condensed_str(), self.total().condensed_str() )
