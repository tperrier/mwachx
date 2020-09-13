#!/usr/bin/python
 # -*- coding: utf-8 -*-
from argparse import Namespace
import datetime, openpyxl as xl, os
import code
import operator, collections
import re
import unicodecsv as csv
import math

# Django imports
from argparse import Namespace
from django.core.management.base import BaseCommand, CommandError
from django.db import models , connection
from django.utils import timezone

# Local imports
import backend.models as back
import contacts.models as cont
import utils
import report_utils
from utils.xl import xl_add_header_row , xl_style_current_row , make_column , bold_font

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
        print_parser.add_argument('-x', '--success-times', action='store_true', default=False, help='print success times report')
        print_parser.add_argument('-u', '--message-status', default=None, const='all',
            choices=('day','week','cur_week','month','year','all'),nargs='?', help='print message status')
        print_parser.add_argument('--delivery-source',action='store_true',default=False,help='print delivery source statistics')
        print_parser.add_argument('--topics',action='store_true',default=False,help='incoming message topics')
        print_parser.add_argument('--msg-counts',action='store_true',default=False,help='print counts by auto type')
        print_parser.add_argument('--sim-count', action='store_true', default=False, help='print information on sim count')
        print_parser.add_argument('--weeks',default=5,type=int,help='message history weeks (default 5)')
        print_parser.set_defaults(action='print_stats')

        xlsx_parser = subparsers.add_parser('xlsx',cmd=parser.cmd,help='create xlsx reports')
        xlsx_parser.add_argument('-t','--visit',action='store_true',default=False,help='create visit report')
        xlsx_parser.add_argument('-d','--detail',action='store_true',default=False,help='create detail report')
        xlsx_parser.add_argument('-a','--all',action='store_true',default=False,help='create all reports')
        xlsx_parser.add_argument('-i','--interaction',action='store_true',default=False,help='create participant interaction report')
        xlsx_parser.add_argument('-m','--messages',action='store_true',default=False,help='create system message dump')
        xlsx_parser.add_argument('-n','--anonymous',action='store_true',default=False,help='create anonymous message dump')
        xlsx_parser.add_argument('-w','--weekly',action='store_true',default=False,help='create weakly stats report')
        xlsx_parser.add_argument('-c','--conversations',action='store_true',default=False,help='create conversations report')
        xlsx_parser.add_argument('-s','--miss-streak',action='store_true',default=False,help='create miss streak report')
        xlsx_parser.add_argument('--dir',default='ignore',help='directory to save report in')
        xlsx_parser.add_argument('args',nargs='*',help='extra arguments in key:value pairs')
        xlsx_parser.set_defaults(action='make_xlsx')

        csv_parser = subparsers.add_parser('csv',cmd=parser.cmd,help='create csv reports')
        csv_parser.add_argument('--dir',default='ignore',help='directory to save csv in')
        csv_parser.add_argument('name',help='csv report type',
            choices=(
                'hiv_messaging','enrollment','messages','edd','delivery', 'participant_week',
                'sae','visits','msg_dump','hiv_statuschange','participant_dump','connection_info',
                'sms_status','languages',
            )
        )
        csv_parser.set_defaults(action='make_csv_name')

    def handle(self,*args,**options):

        start_time = datetime.datetime.now()
        self.stdout.write( 'Reports Action: {}'.format(options['action']) )

        self.printed = False
        self.options = options
        self.options['args'] = args
        getattr(self,options['action'])()

        time_delta = (datetime.datetime.now() - start_time).total_seconds() / 60
        print "Quries: {}  Min: {}".format( len(connection.queries), time_delta )

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
        if self.options['topics']:
            self.print_report('msg_topics')
        if self.options['msg_counts']:
            self.print_report('msg_counts')
        if self.options['message_status'] is not None:
            self.print_message_status()
        if self.options['success_times']:
            self.print_success_times()
        if self.options['sim_count']:
            self.print_sim_counts()

    def print_report(self,report):
        report_modual = getattr(report_utils,report)
        report_modual.print_report(self)

    # SEC::XLSX Helper Functions
    def make_xlsx(self):

        kwargs = {'mode':'meta'}
        if self.options['args']:
            args = self.options['args']
            kwargs.update({arg.split(':')[0]:arg.split(':')[1] for arg in args})

        workbook_columns = {}
        if self.options['visit'] or self.options['all']:
            workbook_columns['visit'] =  visit_columns
        if self.options['detail'] or self.options['all']:
            workbook_columns['detail'] =  detail_columns
        if self.options['interaction']:
            workbook_columns['interaction'] =  interaction_columns
            interaction_columns.queryset = make_interaction_columns()
        if self.options['messages']:
            # workbook_columns['messages'] = system_message_columns
            # system_message_columns.queryset = make_system_message_columns()
            make_message_wb(**kwargs)
        if self.options['weekly']:
            make_weekly_wb()
        if self.options['anonymous']:
            make_anonymous_wb()
        if self.options['conversations']:
            make_conversations_wb()
        if self.options['miss_streak']:
            make_miss_streak_count_wb()

        for name , columns in workbook_columns.items():

            wb = xl.workbook.Workbook()
            today = datetime.date.today()
            file_name = today.strftime('mWaChX_{}_%Y-%m-%d.xlsx').format(name)
            xlsx_path_out = os.path.join(self.options['dir'],file_name)
            self.stdout.write( "Making xlsx file {}".format(xlsx_path_out) )

            if hasattr(columns,'facility_sheet'):
                make_facility_worksheet(columns,wb.active,'ahero')
                make_facility_worksheet(columns,wb.create_sheet(),'bondo')
                make_facility_worksheet(columns,wb.create_sheet(),'mathare')
                make_facility_worksheet(columns,wb.create_sheet(),'siaya')
                make_facility_worksheet(columns,wb.create_sheet(),'rachuonyo')
                make_facility_worksheet(columns,wb.create_sheet(),'riruta')
            else:
                make_worksheet(columns,wb.active,columns.queryset)

            wb.save(xlsx_path_out)

    # SEC::Start CSV Functions
    def make_csv_name(self):
        file_path = getattr(self,'make_{}_csv'.format(self.options['name']))()
        print "Done:" , file_path


    ########################################
    # Start Print Functions
    ########################################

    def send_times(self):

        self.print_header("Participant Send Times")

        c_all = cont.Contact.objects_no_link.all().order_by('send_day','send_time')
        time_counts = c_all.filter(study_group='two-way').values('send_day','send_time') \
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

        self.print_header('Language of Messages (participant,nurse)')

        message_groups = cont.Message.objects.order_by().filter(contact__study_group='two-way',is_system=False)\
            .prefetch_related('contact').values('languages','contact__language','is_outgoing')\
            .exclude(languages='').annotate(count=models.Count('id',distinct=True))

        # Piviot Group Counts
        language_counts = collections.defaultdict(LanguageMessageRow)
        for g in message_groups:
            language_str = ','.join( sorted( s[0] if s!= 'sheng' else 'h' for s in g['languages'].split(';') ) )
            # language_counts[g['languages']][g['contact__language']][g['is_outgoing']] += g['count']
            language_counts[language_str][g['contact__language']][g['is_outgoing']] += g['count']

        # Print Group Counts
        self.stdout.write( "{:^12}{:^12}{:^12}{:^12}{:^12}".format("","English","Swahili","Luo","Total") )
        total_row = LanguageMessageRow()
        for language, row in language_counts.items():
            self.stdout.write( "{0:^12}{1[english]:^12}{1[swahili]:^12}{1[luo]:^12}{2:^12}".format(
                language, row, row.total()
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

        self.stdout.write( 'Furthest past EDD')
        for p in edd[:5]:
            self.stdout.write( "\t{0.study_id} {0.due_date} {0.study_group} (weeks {1:.0f})".format(
                p, p.delta_days() / 7
            ) )
        self.stdout.write( '\n')

        # Calculate EDD to Delivery Date offset delta
        dd = c_all.filter(delivery_date__isnull=False).order_by('delivery_date')
        self.stdout.write( 'Found {:d} post-partum participants'.format(dd.count()) )
        self.stdout.write( 'Furthest from delivery date - (id due_date delivery_date)')
        for p in dd[:5]:
            self.stdout.write( "\t{0.study_id} {0.due_date} {0.delivery_date}  {0.study_group} (weeks {1:.0f})".format(
                p, p.delta_days() / 7
            ) )
        self.stdout.write( '\n')

        # Add edd to dd delta seconds
        dd_min , dd_max , dd_total , dd_count = None , None , 0 , dd.count()
        dd_hist = [0 for _ in range(-10,11)]
        for p in dd:
            p.dd_delivery_delta = (p.delivery_date - p.due_date).total_seconds()
            if dd_min is None or dd_min.dd_delivery_delta > p.dd_delivery_delta:
                dd_min = p
            if dd_max is None or dd_max.dd_delivery_delta < p.dd_delivery_delta:
                dd_max = p
            dd_total += p.dd_delivery_delta
            dd_weeks = int(p.dd_delivery_delta / 604800) + 10
            if dd_weeks < 0:
                dd_weeks = 0
            elif dd_weeks > 20:
                dd_weeks = 20
            dd_hist[dd_weeks] += 1

        self.stdout.write( 'Min {:s} (weeks {:.0f})  Max: {:s} (weeks {:.0f}) Average: {:f}'.format(
            dd_min.study_id , dd_min.dd_delivery_delta/604800 ,
            dd_max.study_id , dd_max.dd_delivery_delta/604800,
            dd_total/(dd_count*604800)
        ) )

        table = ""
        for c in range(-10,11):
            table += ' {:2.0f} '.format(c)
        table += '\n' + '----'*21 + '\n'
        for c in dd_hist:
            table += ' {:2.0f} '.format(c)
        self.stdout.write(table)

        # Add ANC Signup Week
        ll = c_all.filter(study_group='two-way',delivery_date__isnull=False)
        # ll = c_all.filter(delivery_date__isnull=False)
        ll_min , ll_max , ll_total , ll_count = None , None , 0 , ll.count()
        ll_hist = collections.Counter()
        for p in ll:
            p.ll_due_delta = (p.delivery_date - p.created.date()).days
            if ll_min is None or ll_min.ll_due_delta > p.ll_due_delta:
                ll_min = p
            if ll_max is None or ll_max.ll_due_delta < p.ll_due_delta:
                ll_max = p
            ll_total += p.ll_due_delta
            ll_hist[ p.ll_due_delta // 7 ] += 1

        self.stdout.write( '\n\n ****   Signup to EDD Delta   ***' )
        self.stdout.write( 'Min {:s} (weeks {:.0f})  Max: {:s} (weeks {:.0f}) Average: {:f}'.format(
            ll_min.study_id , ll_min.ll_due_delta // 7 ,
            ll_max.study_id , ll_max.ll_due_delta // 7,
            ll_total/(ll_count * 7)
        ) )

        table = ""
        for c in range( min(ll_hist), 43 ):
            table += ' {:2.0f} '.format(c)
        table += '\n' + '----'*21 + '\n'
        for c in range( min(ll_hist), 43):
            table += ' {:2.0f} '.format(ll_hist[c])
        self.stdout.write(table)

        # Add delivery to loss delta (weeks)
        ll = c_all.filter(loss_date__isnull=False)
        ll_min , ll_max , ll_total , ll_count = None , None , 0 , ll.count()
        ll_hist = collections.Counter()
        for p in ll:
            p.ll_notification_delta = p.delivery_notification_delta
            if ll_min is None or ll_min.ll_notification_delta > p.ll_notification_delta:
                ll_min = p
            if ll_max is None or ll_max.ll_notification_delta < p.ll_notification_delta:
                ll_max = p
            ll_total += p.ll_notification_delta
            ll_hist[ p.ll_notification_delta // 7 ] += 1

        self.stdout.write( '\n\n ****   Delivery to Loss Date  ***' )
        self.stdout.write( 'Min {:s} (weeks {:.0f})  Max: {:s} (weeks {:.0f}) Average: {:f}'.format(
            ll_min.study_id , ll_min.ll_notification_delta // 7 ,
            ll_max.study_id , ll_max.ll_notification_delta // 7,
            ll_total/(ll_count * 7)
        ) )

        table = ""
        for c in range( 0 , max(ll_hist.keys())+1 ):
            table += ' {:2.0f} '.format(c)
        table += '\n' + '----'*21 + '\n'
        for c in range( 0 , max(ll_hist.keys())+1 ):
            table += ' {:2.0f} '.format(ll_hist[c])
        self.stdout.write(table)

        # Add stop date hist
        ss = c_all.filter(statuschange__new='stopped')
        ss_min , ss_max , ss_total , ss_count = None , None , 0 , ss.count()
        ss_hist = collections.Counter()
        for p in ss:
            p.ss_notification_delta = p.stopped_study_delta
            if ss_min is None or ss_min.ss_notification_delta > p.ss_notification_delta:
                ss_min = p
            if ss_max is None or ss_max.ss_notification_delta < p.ss_notification_delta:
                ss_max = p
            ss_total += p.ss_notification_delta
            ss_hist[ p.ss_notification_delta // 28 * 4 ] += 1

        self.stdout.write( '\n\n ****   Study Start To Stop Weeks  ***' )
        self.stdout.write( 'Min {:s} (weeks {:.0f})  Max: {:s} (weeks {:.0f}) Average: {:f}'.format(
            ss_min.study_id , ss_min.ss_notification_delta // 7 ,
            ss_max.study_id , ss_max.ss_notification_delta // 7,
            ss_total/(ss_count * 7)
        ) )

        table = ""
        for c in range( 0 , max(ss_hist.keys())+1, 4 ):
            table += ' {:2.0f} '.format(c)
        table += '\n' + '----'*21 + '\n'
        for c in range( 0 , max(ss_hist.keys())+1, 4 ):
            table += ' {:2.0f} '.format(ss_hist[c])
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

    def print_success_times(self):

        self.print_header('Success Times')

        participant_message_counts = cont.Contact.objects_no_link.annotate_messages().order_by('-msg_missed')[:13]
        def display_phone_number(num):
            participant = participant_message_counts[num-1]
            return " |\t{!r:<40} O: {:<3} D: {:<3} M: {:<3} I: {:<3}".format(
                participant,
                participant.msg_outgoing,
                participant.msg_delivered,
                participant.msg_missed,
                participant.msg_incoming
            )

        self.stdout.write('\n')
        intervals = [
            ['',0],
            ['<10s',10],
            ['<30s',30],
            ['<1m',60],
            ['<5m',300],
            ['<10m',600],
            ['<30m',1800],
            ['<1h',3600],
            ['<2h',7200],
            ['<4h',14400],
            ['<8h',28800],
            ['<16h',57600],
            ['<24h',86400],
            ['>24h',604800]
        ]

        # Add success_dt and filter messages from start of collection: Nov 30, 2016
        messages = cont.Message.objects.exclude(external_status='Failed').add_success_dt()
        for i in range(1,len(intervals)):
            count = messages.filter(
                success_dt__range=(intervals[i-1][1],intervals[i][1])
            ).count()
            intervals[i].append(count)
            self.stdout.write( '  {:>8}: {:<4}{:>15}'.format(
                intervals[i][0],
                count,
                display_phone_number(i)
            ))

        print "\tTotal (since Nov 30, 2016): {} Longest Wait: {} (h)".format(
            messages.filter(success_dt__isnull=False).count(),
            messages.first().success_dt/3600.0)

    def print_sim_counts(self):
        self.print_header('SIM Counts')

        counts = collections.defaultdict(int)
        for c in cont.Contact.objects_no_link.annotate_messages():
            if c.sim_count <= 1:
                continue
            counts[c.study_group] += 1
            print "{0.study_id} - {0.facility} - {0.study_group} - {1}: {0.msg_outgoing}-{0.msg_incoming}".format(c,c.created.date())
            for conn in c.connection_set.all():
                first_message = cont.Message.objects.filter(connection=conn).last()
                print "{} - {} {}: {}-{}".format(
                    conn, conn.is_primary,
                    first_message.created.date() if first_message is not None else None,
                    cont.Message.objects.filter(connection=conn,is_outgoing=True).count(),
                    cont.Message.objects.filter(connection=conn,is_outgoing=False).count(),
                )
            print '-'*40 , '\n'

        print counts

    def print_message_status(self):

        self.print_header('All Messages By Status')

        # Print message status
        print message_status_groups(delta=self.options['message_status'])

        print "Other Types"
        status_groups = cont.Message.objects.order_by().values('external_status'). \
            exclude(external_status__in=('Success','Sent','Failed')).exclude(is_outgoing=False). \
            annotate(count=models.Count('external_status'))
        for group in status_groups:
            print "\t{0[external_status]:<30}: {0[count]}".format(group)
        print "\t{:<30}: {}".format("Total",sum( g['count'] for g in status_groups ) )

        print "\nFailed Reasons"
        reasons = collections.Counter()
        for msg in cont.Message.objects.filter(is_outgoing=True).exclude(external_status__in=('Success','Sent')):
            reasons[msg.external_data.get('reason','No Reason')] += 1
        for reason , count in reasons.items():
            print "\t{:<20}: {}".format(reason,count)
        print "\t{:<20}: {}".format("Total",sum( reasons.values() ) )

    def print_header(self,header):
        if self.printed:
            self.stdout.write("")
        self.printed = True

        self.stdout.write( "-"*30 )
        self.stdout.write( "{:^30}".format(header) )
        self.stdout.write( "-"*30 )

    ########################################
    # SEC::Start CSV Functions
    ########################################

    def make_connection_info_csv(self):
        ''' Basic csv dump of connection info '''
        connections = cont.Connection.objects.filter(contact__isnull=False).order_by('contact__created')
        file_path = os.path.join(self.options['dir'],'connections.csv')
        csv_writer = csv.writer(open(file_path,'w'))
        csv_writer.writerow( ['id','created','sims','group','facility','primary',
            'first','last','total','participant','system','success','first_success','last_success'
            ])
        for conn in connections:
            total = conn.message_set.count()
            row = [
                conn.contact.study_id,
                conn.contact.created.date(),
                conn.contact.sim_count,
                conn.contact.study_group,
                conn.contact.facility,
                1 if conn.is_primary is True else 0,
                conn.message_set.last().created.date() if total > 0 else '' ,
                conn.message_set.first().created.date() if total > 0 else '',
                total,
                conn.message_set.filter(is_outgoing=False).count(),
                conn.message_set.filter(is_system=True).exclude(translation_status='cust').count(),
                conn.message_set.filter(is_system=True,external_status='Success').exclude(translation_status='cust').count(),
                sum(1 for m in conn.message_set.filter(is_system=True).exclude(translation_status='cust').order_by('created')[:5] if m.external_status == 'Success'),
                sum(1 for m in conn.message_set.filter(is_system=True).exclude(translation_status='cust').order_by('-created')[:5] if m.external_status == 'Success'),
            ]
            csv_writer.writerow(row)

        return file_path

    def make_sms_status_csv(self):
        ''' Basic csv dump of connection info '''
        file_path = os.path.join(self.options['dir'],'sms_status.csv')
        csv_writer = csv.writer(open(file_path,'w'))
        status_keys = [
        'Nurse','Participant','System', 'Spam',
        'Success', 'Sent', 'Failed','None',
        'AbsentSubscriber',
        'UserDoesNotExist',
        'DeliveryFailure',
        'UserNotProvisioned',
        'SystemFailure',
        'Message Rejected By Gateway',
        'RejectedByGateway',
        'UserMTCallBarred',
        'GatewayError',
        'Rejected',
        'Could Not Send',
        'Unexpected Gateway Error',
        'UserBusyForMTSms',
        ]

        def get_default_row():
            return {key:0 for key in status_keys}
        weeks = collections.defaultdict(get_default_row)

        def get_msg_week(msg):
            created = msg.created.date()
            return str(created - datetime.timedelta(days=created.isoweekday()%7))

        messages = cont.Message.objects.all().prefetch_related('contact')
        for msg in messages:
            week = weeks[get_msg_week(msg)]
            if msg.contact is None:
                week['Spam'] += 1
            elif msg.contact.study_group != 'two-way':
                continue
            elif msg.is_system:
                week['System'] += 1
                if msg.external_status in ['Success', 'Sent']:
                    week[msg.external_status] += 1
                else:
                    week['Failed'] += 1
                    week[str(msg.reason)] += 1
            elif msg.is_outgoing:
                week['Nurse'] += 1
            else:
                week['Participant'] += 1

        # Write header row
        csv_writer.writerow( ['week'] + status_keys )
        # write all weeks
        for week in sorted(weeks.keys()):
            csv_writer.writerow([week] + [weeks[week][key] for key in status_keys])

        return file_path

    def make_languages_csv(self):

        file_path = os.path.join(self.options['dir'],'language_prefs.csv')
        csv_writer = csv.writer(open(file_path,'w'))

        contacts = cont.Contact.objects_no_link.annotate(
            msgs_sent=utils.sql_count_when(message__is_outgoing=False),
            msgs_system=utils.sql_count_when(message__is_system=True),
        ).order_by('facility','study_group','language','study_id')

        def add_stats(c):
            c.msgs_english , c.msgs_swahili, c.msgs_luo, c.msgs_sheng = 0 , 0 , 0 ,0
            for m in c.message_set.all():
                if 'english' in m.languages:
                    c.msgs_english += 1
                if 'swahili' in m.languages:
                    c.msgs_swahili += 1
                if 'luo' in m.languages:
                    c.msgs_luo += 1
                if 'sheng' in m.languages:
                    c.msgs_sheng += 1
            return c

        columns = collections.OrderedDict([
            ('study_id','study_id'),
            ('facility','facility'),
            ('study_group','study_group'),
            ('language','language'),
            ('msgs_sent','msgs_sent'),
            ('msgs_system','msgs_system'),
            ('msgs_english','msgs_english'),
            ('msgs_swahili','msgs_swahili'),
            ('msgs_luo','msgs_luo'),
            ('msgs_sheng','msgs_sheng'),
        ])
        make_csv(columns,[add_stats(c) for c in contacts],file_path)
        return file_path

    def make_hiv_messaging_csv(self):
        ''' Basic csv dump of hiv messaging status '''
        columns = collections.OrderedDict([
            ('study_id','study_id'),
            ('status','status'),
            ('hiv_messaging','hiv_messaging'),
            ('hiv_disclosed', null_boolean_factory('hiv_disclosed')),
            ('phone_shared', null_boolean_factory('phone_shared')),
        ])

        contacts = cont.Contact.objects.all().order_by('study_id')
        file_path = os.path.join(self.options['dir'],'hiv_messaging.csv')

        make_csv(columns,contacts,file_path)
        return file_path

    def make_hiv_statuschange_csv(self):
        ''' Basic csv dump of hiv messaging status changes '''
        columns = collections.OrderedDict([
            ('study_id','contact.study_id'),
            ('status','contact.status'),
            ('old','old'),
            ('new', 'new'),
            ('date','created'),
            ('since_enrollment', lambda obj: obj.created - obj.contact.created ),
        ])
        status_changes = cont.StatusChange.objects.filter(type='hiv')

        file_path = os.path.join(self.options['dir'],'hiv_status_changes.csv')

        make_csv(columns,status_changes,file_path)
        return file_path

    def make_visits_csv(self):
        ''' Basic csv dump of visit history for all participants '''
        columns = collections.OrderedDict([
            ('study_id',operator.attrgetter('participant.study_id')),
            ('type','visit_type'),
            ('status','status'),
            ('scheduled','scheduled'),
            ('arrived','arrived'),
            ('notify_count','notify_count'),
            ('notification_date','notification_last_seen'),
            ('sms_count','missed_sms_count'),
            ('sms_date','missed_sms_last_sent'),
            ('viewed','notify_count'),
        ])

        visits = cont.Visit.objects.all().order_by('participant__study_id').prefetch_related('participant')
        today = datetime.date.today()
        file_name = today.strftime('visit_dump_%Y-%m-%d.csv')
        file_path = os.path.join(self.options['dir'],file_name)
        make_csv(columns,visits,file_path)
        return file_path

    def make_enrollment_csv(self):
        """ CSV Report of enrollment per week """
        c_all = cont.Contact.objects.all()

        enrollment_counts = collections.OrderedDict()

        for c in c_all:
            key = c.created.strftime('%Y-%U')
            try:
                enrollment_counts[key][c.facility] += 1
            except KeyError as e:
                enrollment_counts[key] = FacilityRow()
                enrollment_counts[key][c.facility] += 1

        file_path = os.path.join(self.options['dir'],'enrollment.csv')

        with open( file_path , 'wb') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Header Row
            csv_writer.writerow( ["Week"] + FacilityRow.columns + ["Total"] )
            total_row = FacilityRow()
            for week , enrollment in enrollment_counts.items():
                csv_writer.writerow( [week] + list(enrollment) + [enrollment.total()] )
                total_row += enrollment
            csv_writer.writerow( ['Total'] + list(total_row) + [total_row.total()] )

        return file_path

    def make_messages_csv(self):
        """ Messages per week csv """

        m_all = cont.Message.objects.all().order_by('created')

        msg_type_counts = collections.OrderedDict()

        for msg in m_all:
            key = msg.created.strftime('%Y-%U')
            try:
                msg_type_counts[key][msg.msg_type] += 1
            except KeyError as e:
                msg_type_counts[key] = MessageTypeRow()
                msg_type_counts[key][msg.msg_type] += 1

        file_path = os.path.join(self.options['dir'],'messages.csv')

        with open( file_path , 'wb') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write Header
            csv_writer.writerow( ["Week"] + MessageTypeRow.columns + ["Total"] )
            total_row = MessageTypeRow()
            for week , msg_types in msg_type_counts.items():
                csv_writer.writerow( [week] + list(msg_types) + [msg_types.total()] )
                total_row += msg_types
            csv_writer.writerow( ['Total'] + list(total_row) + [total_row.total()] )

        return file_path

    def make_msg_dump_csv(self):
        """ Dump stats for each incomming message to csv """
        mode = 'spam'
        if mode == 'client':
            columns = collections.OrderedDict([
                ('timestamp','created'),
                ('study_id','contact.study_id'),
                ('facility','contact.facility'),
                ('since_enrollment', lambda obj: int((obj.created.date() - obj.contact.created.date()).total_seconds() / 86400) ),
                ('since_delivery', lambda obj: int((obj.created.date() - obj.contact.delivery_date).total_seconds() / 86400)
                    if obj.contact.delivery_date is not None else '' ),
                ('topic','topic'),
                ('related','is_related'),
                ('languages','languages'),
                ('text','display_text'),
                ('chars',lambda m: len(m.text)),
                ('words',lambda m: len( m.text.split() )),
                ('text_raw','text'),
            ])
            m_all = cont.Message.objects.filter(is_outgoing=False,contact__study_group='two-way') \
                .order_by('contact__study_id','created').prefetch_related('contact')
        elif mode == 'nurse':
            columns = collections.OrderedDict([
                ('timestamp','created'),
                ('study_id','contact.study_id'),
                ('facility','contact.facility'),
                ('since_enrollment', lambda obj: int((obj.created.date() - obj.contact.created.date()).total_seconds() / 86400) ),
                ('since_delivery', lambda obj: int((obj.created.date() - obj.contact.delivery_date).total_seconds() / 86400)
                    if obj.contact.delivery_date is not None else '' ),
                ('languages','languages'),
                ('text','display_text'),
                ('chars',lambda m: len(m.text)),
                ('words',lambda m: len( m.text.split() )),
                ('reply',lambda m: 1 if m.parent else 0),
                ('text_raw','text'),
            ])
            m_all = cont.Message.objects.filter(is_outgoing=True,is_system=False,contact__study_group='two-way') \
                .exclude(translation_status='cust').order_by('contact__study_id','created').prefetch_related('contact')
        elif mode == 'system':
            columns = collections.OrderedDict([
                ('send_base','send_base'),
                ('send_offset','send_offset'),
                ('group','group'),
                ('condition','condition'),
                ('hiv', lambda m: 1 if m.hiv_messaging else 0),
                ('text', lambda m: m.english[39:] if m.english[0] == '{' else m.english),
            ])
            m_all = back.AutomatedMessage.objects.all().order_by('send_base','send_offset','group','condition','hiv_messaging')
        elif mode == 'spam':
            columns = collections.OrderedDict([
                ('id','id'),
                ('timestamp','created'),
                ('number','connection.identity'),
                ('text','display_text'),
            ])
            m_all = cont.Message.objects.filter(is_outgoing=False,contact__isnull=True).order_by('created')
        elif mode == 'all':
            columns = collections.OrderedDict([
                ('timestamp','created'),
                ('study_id','contact.study_id'),
                ('sent_by','sent_by'),
                ('status','external_status'),
                ('topic','topic'),
                ('related','related'),
            ])
            m_all = cont.Message.objects.filter(contact__study_group='two-way').order_by('contact_study_id','created').prefetch_related('contact')

        file_path = os.path.join(self.options['dir'],'message_dump_{}.csv'.format(mode))
        make_csv(columns,m_all,file_path)
        return file_path

    def make_participant_dump_csv(self):
        """ Dump stats for each participant """
        columns = collections.OrderedDict([
            ('id','study_id'),
            ('created',lambda c: c.created.date()),
            ('facility','facility'),
            ('group','study_group'),
            ('shared',lambda c: 1 if c.phone_shared else 0) ,
            ('validation',lambda c: 1 if c.is_validated else 0),
            ('age','age'),
        ])
        p_all = cont.Contact.objects.all()
        file_path = os.path.join(self.options['dir'],'participant_dump.csv')
        make_csv(columns,p_all,file_path)
        return file_path

    def make_edd_csv(self):
        """ Make report of delivery_date to edd time delta in weeks """

        c_all = cont.Contact.objects.filter(delivery_date__isnull=False).exclude(status__in=('loss','sae'))

        edd_deltas = collections.Counter( (c.delivery_date - c.due_date).days / 7 for c in c_all )
        weeks = sorted(edd_deltas.keys())

        file_path = os.path.join(self.options['dir'],'edd_deltas.csv')

        with open( file_path , 'wb') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write Header
            csv_writer.writerow( ("Week" , "Count") )
            for week in range( weeks[0] , weeks[-1] + 1):
                csv_writer.writerow( (week , edd_deltas[week]) )

        return file_path

    def make_delivery_csv(self):
        """ Create csv of time delta in weeks between delivery and delivery notification """
        c_all = cont.Contact.objects.filter(delivery_date__isnull=False).exclude(status__in=('loss','sae'))

        delivery_deltas = collections.defaultdict( GroupRowCount )
        max_week = 0
        for c in c_all:
            delta = c.delivery_delta()
            delta_weeks = delta / 7 if delta is not None else 'none'
            delivery_deltas[delta_weeks][c.study_group] += 1
            if delta is not None and delta < 0:
                print c.study_id, c, c.delivery_date , c.status
            if delta_weeks > max_week and delta is not None:
                max_week = delta_weeks

        file_path = os.path.join(self.options['dir'],'delivery_deltas.csv')

        with open( file_path , 'wb') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write Header
            csv_writer.writerow( ("Week" , "Control" , "One-Way", "Two-Way", "Total") )
            total_row = GroupRowCount()
            for week in range(max_week + 1):
                csv_writer.writerow( [week] + list(delivery_deltas[week]) + [delivery_deltas[week].total()] )
                total_row += delivery_deltas[week]
            csv_writer.writerow( ["Total"] + list(total_row) + [total_row.total()] )

        return file_path

    def make_sae_csv(self):

        loss = cont.Contact.objects.filter(loss_date__isnull=False)

        loss_deltas = collections.defaultdict( GroupRowCount )
        max_week = 0
        for c in loss:
            loss_notify = c.statuschange_set.filter(
                models.Q(new='loss') | models.Q(new='sae')
            ).first().created.date()
            delta_weeks = (loss_notify - c.loss_date).days / 7
            loss_deltas[delta_weeks][c.study_group] += 1
            if delta_weeks > max_week:
                max_week = delta_weeks

        file_path = os.path.join(self.options['dir'],'loss_deltas.csv')

        with open( file_path , 'wb') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write Header
            csv_writer.writerow( ("Week" , "Control" , "One-Way", "Two-Way", "Total") )
            total_row = GroupRowCount()
            for week in range(max_week + 1):
                csv_writer.writerow( [week] + list(loss_deltas[week]) + [loss_deltas[week].total()] )
                total_row += loss_deltas[week]
            csv_writer.writerow( ["Total"] + list(total_row) + [total_row.total()] )

        return file_path

    def make_participant_week_csv(self):
        # Report with number of system, participant and nurse messages per week

        file_path = os.path.join(self.options['dir'],'participant_msg_per_week.csv')
        csv_fp = open(file_path,'w')
        csv_writer = csv.writer(csv_fp)

        # Header Row
        csv_writer.writerow( ('id','group','loss', 'anc_week',
                            'study_week','delivery_week','loss_week',
                            'participant','nurse','system',
                            'delivered','unkown','failed',
                            'n_delivered','n_unkown','n_failed',
                            # 'start_art','on_art',
                            'antenatal-concerns','delivery-concerns','infant-health','family-planing','adherence','visits','other',
                            ) )
        def week_start(d):
            return d - datetime.timedelta(days=d.weekday()+1)
        def week_end(d):
            return d + datetime.timedelta(days=6-d.weekday())
        def m_status(m):
            return {'Success':'delivered','Sent':'unkown'}.get(m.external_status,'failed')

        participants = cont.Contact.objects.exclude(study_group='control').prefetch_related('message_set')
        # participants = cont.Contact.objects.filter(study_id__in=['0003','0803']).prefetch_related('message_set')
        for p in participants:

            p.study_start = week_start(p.created.date())
            p.delivery_start = week_start(p.delivery_date if p.delivery_date else p.due_date)
            p.study_end = week_end( p.last_msg_system )

            week_range = (p.study_end - p.study_start).days // 7 + 1
            delivery_offset = (p.delivery_start - p.study_start).days // 7
            loss_offset = (p.loss_date - p.study_start).days // 7 if p.loss_date else None
            if week_range < 90:
                print 'Weeks less than 90', week_range
                continue

            counts = [ dict(system=0,participant=0,nurse=0,
                            delivered=0,unkown=0,failed=0,
                            n_delivered=0,n_unkown=0,n_failed=0,
                            antenatal_concerns=0,delivery_concerns=0,infant_health=0,family_planing=0,adherence=0,visits=0,other=0,
                             )
                        for _ in range( week_range )
                    ]
            for m in p.message_set.all():

                week = ( week_start(m.created.date()) - p.study_start ).days // 7
                anc_week = week - delivery_offset
                # if week - delivery_offset >= 110  or anc_week < -30 or week >= week_range:
                #     continue
                if week >= week_range:
                    continue

                if m.is_outgoing is True:
                    if m.is_system is True:
                        counts[week]['system'] += 1
                        counts[week][m_status(m)] += 1
                    else:
                        counts[week]['nurse'] += 1
                        counts[week]['n_%s'%m_status(m)] += 1
                else:
                    counts[week]['participant'] += 1

                    """
                            Reports Action: print_stats
                    antenatal-concerns    885      9.92     95.00
                    delivery-concenrs     732      8.21     95.00
                    infant-health        1484     16.63     94.00
                        immunization          157      1.76     91.00
                    family-planing        825      9.25     95.00
                    adherence            1638     18.36     91.00
                        side-effects          147      1.65     90.00
                    visits               1959     21.96     94.00
                    other                 903     10.12     76.00
                        validation            166      1.86    100.00
                        sexual-behavior        24      0.27     91.00
                    """
                    if m.topic == 'antenatal-concerns':
                        counts[week]['antenatal_concerns'] += 1
                    elif m.topic == 'delivery-concenrs':
                        counts[week]['delivery_concerns'] += 1
                    elif m.topic == 'infant-health' or m.topic == 'immunization':
                        counts[week]['infant_health'] += 1
                    elif m.topic == 'family-planing':
                        counts[week]['family_planing'] += 1
                    elif m.topic == 'adherence' or m.topic == 'side-effects':
                        counts[week]['adherence'] += 1
                    elif m.topic == 'visits':
                        counts[week]['visits'] += 1
                    else:
                        counts[week]['other'] += 1



            for idx , row in enumerate(counts):

                csv_writer.writerow( (p.study_id, p.study_group, p.sae_opt_in_status, delivery_offset,
                            idx , idx - delivery_offset, idx - loss_offset if loss_offset else None,
                            row['participant'], row['nurse'], row['system'],
                            row['delivered'], row['unkown'], row['failed'],
                            row['n_delivered'], row['n_unkown'], row['n_failed'],
                            row['antenatal_concerns'],row['delivery_concerns'],row['infant_health'],row['family_planing'],row['adherence'],row['visits'],row['other'],
                            ) )


########################################
# SEC::XLSX Helper Functions
########################################

last_week = datetime.date.today() - datetime.timedelta(days=7)
detail_columns = collections.OrderedDict([
    ('Study ID','study_id'),
    ('Enrolled',lambda c: c.created.date()),
    ('Group','study_group'),
    ('Status','get_status_display'),
    ('HIV','hiv_messaging') ,
    ('Disclosed','hiv_disclosed') ,
    ('Shared','phone_shared') ,
    ('Sec Preg','second_preg'),
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
detail_columns.facility_sheet = True

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
visit_columns.facility_sheet = True

BUCKETS = 4
interaction_columns = collections.OrderedDict([
    ('id','study_id'),

    ('signup', lambda c: c.created.date()),
    ('edd','due_date'),
    ('delivery','delivery_date'),
    ('d_notificaiton','notification_date'),
    ('auto_end','end_auto_messages'),
    ('msg_end','msg_end'),

    ('language','language'),
    ('condition','condition'),
    ('group','study_group'),
    ('facility','facility'),
    ('status','status'),
    ('is_validated','is_validated'),

    ('send_time','send_time'),
    ('send_day','send_day'),

    ('loss_date','loss_date'),
    ('loss_delta','loss_delta'),
    ('opt-in','sae_opt_in_status'),

    ('relationship','relationship_status'),
    ('phone_shared','phone_shared'),
    ('preg_num', 'previous_pregnancies'),
    ('age',lambda c: c.age(signup=True)),
    ('sim_count','sim_count'),

    ('art_delta','delta_art'),
    ('hiv_disclosed','hiv_disclosed'),
    ('hiv_messaging','hiv_messaging'),

    ('weeks','msg_weeks'),

    ('s_anc_wk','system_anc_weeks'),
    ('s_post_wk','system_post_weeks'),
    ('s_baby_wk','system_baby_weeks'),
    ('s_done_wk','system_done_weeks'),
    ('d_anc_wk','delivery_anc_weeks'),
    ('d_post_wk','delivery_post_weeks'),

    ('notification_delta','notification_delta'),
    ('notification_method','delivery_source'),

    ('weeks_active','weeks_active'),
    ('anc_active','weeks_active_anc'),
    ('w26_active','week_26_active'),
    ('p_weeks_active', lambda c: blank_or_percent(c.weeks_active,c.msg_weeks) ),
    ('p_anc_active', lambda c: blank_or_percent(c.weeks_active_anc,c.anc_weeks) ),
    ('p_w26_active', lambda c: blank_or_percent(c.week_26_active,min(c.msg_weeks,26)) ),

    ('outgoing','msg_outgoing'),
    ('system','msg_system'),
    ('nurse','msg_nurse'),

    ('participant','msg_incoming'),
    ('respond_system','respond_system'),
    ('respond_nurse','respond_nurse'),
    ('respond_system_2d','respond_system_2d'),
    ('respond_nurse_2d','respond_nurse_2d'),
    ('respond_none','respond_none'),

    ('msgs_per_week','msgs_per_week'),

    ('system_anc','system_anc'),
    ('nurse_anc','nurse_anc'),
    ('participant_anc','participant_anc'),

    ('visits','visits'),
    ('v_pre_msgs','visit_pre_msgs'),
    ('v_miss_msgs','visit_miss_msgs'),
    ('v_attend_msgs','visit_attend_msgs'),
    ('v_pre_response','visit_pre_response'),
    ('v_miss_response','visit_miss_response'),
    ('v_attend_response','visit_attend_response'),
    ('v_pre_p', lambda c: blank_or_percent(c.visit_pre_response,c.visit_pre_msgs)),
    ('v_miss_p', lambda c: blank_or_percent(c.visit_miss_response,c.visit_miss_msgs)),
    ('v_attend_p', lambda c: blank_or_percent(c.visit_attend_response,c.visit_attend_msgs)),

    ('anc_after', 'anc_after'),
    ('post_after', 'post_after'),
    ('baby_after', 'baby_after'),

    ('avg_ddelta_h','avg_msg_delta'),
    ('avg_ddelta_system_h','avg_msg_delta_system'),
    ('avg_ddelta_nurse_h','avg_msg_delta_nurse'),

    ('avg_length','avg_msg_length'),
    ('avg_length_s','avg_msg_length_system'),
    ('avg_length_n','avg_msg_length_nurse'),
    ('avg_length_p','avg_msg_length_none'),

    ('avg_reply_h','avg_reply'),
    ('avg_reply_s_h','avg_reply_system'),
    ('avg_reply_n_h','avg_reply_nurse'),

    ('max_conversation','max_conversation'),

    ('success','msg_delivered'),
    ('unkown','msg_sent'),
    ('failed','msg_other'),

    ('success_s','success_system'),
    ('unkown_s','unkown_system'),
    ('failed_s','failed_system'),

    ('success_n','success_nurse'),
    ('unkown_n','unkown_nurse'),
    ('failed_n','failed_nurse'),

    ('p_d','percent_delivered'),
    ('p_ds','success_system_percent'),
    ('p_dn','success_nurse_percent'),

    ('reply_d','reply_delivered'),
    ('reply_u','reply_unkown'),
    ('reply_f','reply_failed'),
    ('reply_d_2d','reply_delivered_2d'),
    ('reply_u_2d','reply_unkown_2d'),
    ('reply_f_2d','reply_failed_2d'),

    ('streak_broken','success_after_failure_count'),
    ('streak_success','success_streak'),
    ('streak_unkown','sent_streak'),
    ('streak_missed','miss_streak'),
    ('streak_start','start_streak'),
    ('streak_last','last_miss_streak'),

    ] + [ ("%s%i"%(c,i),"%s%i"%(c,i)) for c in ('d','n') for i in range(1,BUCKETS+1) ]
    + [('a%i'%i,'a%i'%i) for i in range(1,5)]
)
interaction_columns.widths = {
    'B':12, 'C':12, 'D':12, 'E':12, 'F':12, 'G':12, 'P':12,
}

def make_interaction_columns():

    contacts = collections.OrderedDict( (c.id,c) for c in
        # cont.Contact.objects_no_link.filter(study_id__in=['0003','0803']).annotate_messages()
        # cont.Contact.objects_no_link.annotate_messages().order_by('-msg_outgoing')[:20]
        # cont.Contact.objects_no_link.filter(study_group='two-way').annotate_messages().order_by('-msg_failed')[:20]
        cont.Contact.objects_no_link.annotate_messages().order_by('-study_group','-msg_incoming')
    )

    def week_start(d):
        return d - datetime.timedelta(days=d.weekday()+1)
    def week_end(d):
        return d + datetime.timedelta(days=6-d.weekday())

    def week_delta(d1,d2):
        delta = (week_start(d1) - week_start(d2)).days / 7
        # delta = (d1 - d2).days / 7
        return delta if delta >= 0 else delta + 1

    # Add all messages to contacts.messages
    messages = cont.Message.objects.filter(contact__in=contacts.keys()).order_by('created')
    for m in messages:
        if m.contact_id in contacts:
            c = contacts[m.contact_id]
            if hasattr(c,'messages'):
                c.messages.append(m)
            else:
                c.messages = [m]

    for id , c in contacts.items():
        c.start_streak, start_streak_flag = 0 , False
        c.success_streak ,  current_streak = 0 , 0
        c.sent_streak, current_sent_streak = 0 , 0
        c.miss_streak , current_miss_streak = 0 , 0
        c.success_after_failure_count, failure_streak_size = 0 , 5

        c.msg_start =  c.created.date()
        c.msg_end =  c.messages[-1].created.date()
        c.msg_weeks = week_delta(week_end(c.msg_end) , c.msg_start)

        c.visit_pre_msgs, c.visit_miss_msgs, c.visit_attend_msgs , c.visits = 0 , 0 , 0 , c.visit_set.count()
        c.visit_pre_response, c.visit_miss_response, c.visit_attend_response = 0 , 0 , 0

        if c.delivery_date is not None:
            c.notification_delta = max(c.delivery_notification_delta, 0)
            c.notification_date = c.delivery_date + datetime.timedelta(days=c.notification_delta)

            c.anc_end = c.delivery_date
            if c.notification_date < c.due_date:
                c.system_anc_end = c.notification_date
                c.system_post_weeks = 0
            else:
                c.system_anc_end = c.due_date
                c.system_post_weeks = week_delta(c.notification_date,c.due_date)
            c.system_anc_weeks = min( week_delta(c.system_anc_end, c.msg_start), c.msg_weeks)

            c.end_auto_messages = (c.delivery_date + datetime.timedelta(weeks=104))
            c.system_baby_weeks = max(week_delta(c.end_auto_messages, c.notification_date), 0)
            c.system_done_weeks = week_delta(week_end(c.msg_end), c.end_auto_messages)

            c.delivery_anc_weeks = min(week_delta(c.delivery_date, c.msg_start), c.msg_weeks)
            c.delivery_post_weeks = week_delta(c.notification_date, c.delivery_date)

        else:
            c.anc_end = c.due_date
            c.system_anc_weeks = min( week_delta(c.due_date, c.msg_start), c.msg_weeks)
            c.system_post_weeks = max(week_delta(c.msg_end, c.due_date), 0)
            if c.system_post_weeks == 0:
                c.system_post_weeks = ''
            c.end_auto_messages = c.msg_end

            c.system_baby_weeks , c.system_done_weeks = '' , ''
            c.notification_date , c.notification_delta = '' , ''
            c.delivery_anc_weeks , c.delivery_post_weeks = '' , ''

        if c.loss_date is None:
            c.loss_delta = ''
        else:
            c.loss_delta = c.loss_notification_delta
            if c.loss_delta < 0:
                c.loss_delta = 0

        c.anc_weeks = c.delivery_anc_weeks if c.delivery_anc_weeks != '' else c.system_anc_weeks

        msgs_per_week = [ 0 for _ in range( c.msg_weeks + 1 ) ]
        sent_per_week = [ 0 for _ in range( c.msg_weeks + 1 ) ]
        delivered_per_week = [ 0 for _ in range( c.msg_weeks + 1 ) ]

        c.system_anc , c.participant_anc, c.nurse_anc = 0 , 0 , 0
        c.success_system , c.unkown_system , c.failed_system = 0 , 0 , 0
        c.success_nurse , c.unkown_nurse , c.failed_nurse = 0 , 0 , 0

        c.reply_delivered , c.reply_unkown , c.reply_failed = 0 , 0 , 0
        c.reply_delivered_2d , c.reply_unkown_2d , c.reply_failed_2d = 0 , 0 , 0
        c.respond_system , c.respond_nurse , c.respond_none = 0 , 0 , 0
        c.respond_system_2d, c.respond_nurse_2d = 0 , 0
        c.anc_after , c.post_after, c.baby_after = 0 , 0 , 0
        delivery_delta_total_hours , delivery_delta_system_total_hours, delivery_delta_nurse_total_hours = 0 , 0 , 0
        total_characters , total_characters_system , total_characters_nurse , total_characters_none = 0 , 0 , 0 , 0
        reply_delta_system_total_seconds , reply_delta_nurse_total_seconds = 0 , 0

        # # Set up bucket sizes based on how many system messages there are
        # size , rem = divmod( c.msg_system , BUCKETS )
        # bucket_sizes = [ (size+1) for i in range(rem) ] + [size for i in range(BUCKETS-rem)]
        # delivered_buckets = [ 0 for _ in range(BUCKETS)]
        # sent_buckets = [ 0 for _ in range(BUCKETS)]
        # failed_buckets = [ 0 for _ in range(BUCKETS)]
        # count , bucket = 0 , 0

        # Setup Time based buckets: ANC, 6mo, 12mo, 18mo, more
        bucket_sizes = [0] * BUCKETS
        delivered_buckets = [0] * BUCKETS
        not_delivered_buckets = [0] * BUCKETS

        last_outgoing , last_message = None , None

        for m in c.messages:

            msg_week = week_delta( m.created.date(),  c.msg_start)
            msg_is_anc = 1 if m.created.date() < c.anc_end else 0
            # msg_bucket = 0 # ANC bucket
            # if not msg_is_anc:
            #     delivery_wk = week_delta( m.created.date(), c.anc_end)
            #     if delivery_wk < 26: # 6mo bucket
            #         msg_bucket = 1
            #     elif delivery_wk < 52: #12mo bucket
            #         msg_bucket = 2
            #     elif delivery_wk < 78: #18mo bucket
            #         msg_bucket = 3
            #     else: #24mo and greater bucket
            #         msg_bucket = 4
            if msg_week < 26:
                msg_bucket = 0
            elif msg_week < 52:
                msg_bucket = 1
            elif msg_week < 78:
                msg_bucket = 2
            else:
                msg_bucket = 3

            if m.is_outgoing:
                last_outgoing = m

                if 'visit' in m.auto:
                    if 'pre' in m.auto:
                        c.visit_pre_msgs += 1
                    elif 'missed' in m.auto:
                        c.visit_miss_msgs += 1
                    elif 'attend' in m.auto:
                        c.visit_attend_msgs += 1

                # Start Streak
                if not start_streak_flag:
                    if m.external_status == 'Success':
                        c.start_streak += 1
                    else:
                        start_streak_flag = True

                if m.external_status == 'Success':
                    delivery_delta_total_hours += m.delivery_delta if m.delivery_delta else 0
                    current_streak += 1
                    if m.is_system:
                        delivery_delta_system_total_hours += m.delivery_delta if m.delivery_delta else 0
                        c.success_system += 1
                    elif m.translation_status != 'cust':
                        delivery_delta_nurse_total_hours += m.delivery_delta if m.delivery_delta else 0
                        c.success_nurse += 1
                    if current_miss_streak > c.miss_streak:
                        c.miss_streak = current_miss_streak
                    if current_miss_streak >= failure_streak_size: # success after failure streak
                        c.success_after_failure_count += 1
                    current_miss_streak = 0
                else:
                    if m.external_status == 'Sent':
                        if m.is_system:
                            c.unkown_system += 1
                        elif m.translation_status != 'cust':
                            c.unkown_nurse += 1
                    else: # Failed
                        if m.is_system:
                            c.failed_system += 1
                        elif m.translation_status != 'cust':
                            c.failed_nurse += 1
                    current_miss_streak += 1
                    if current_streak > c.success_streak:
                        c.success_streak = current_streak
                    current_streak = 0

                if m.external_status == 'Sent':
                    current_sent_streak += 1
                else:
                    if current_sent_streak > c.sent_streak:
                        c.sent_streak = current_sent_streak
                    current_sent_streak = 0

                if m.is_system and m.translation_status != 'cust':
                    sent_per_week[msg_week] += 1
                    bucket_sizes[msg_bucket] += 1
                    c.system_anc += msg_is_anc
                    if m.external_status == 'Success':
                        delivered_buckets[msg_bucket] += 1
                        delivered_per_week[msg_week] += 1
                    else:
                        not_delivered_buckets[msg_bucket] += 1
                    if m.created.date() > c.anc_end and m.auto.startswith('edd'):
                        if not '-' in m.auto.split('.')[-1]:
                            c.anc_after += 1
                        else:
                            c.post_after += 1
                    if c.loss_date is not None and m.created.date() > c.loss_date and 'nbaby' not in m.auto:
                        c.baby_after += 1

                else:
                    c.nurse_anc += msg_is_anc

            else: # incoming message

                total_characters += len(m.text)
                c.participant_anc += msg_is_anc
                msgs_per_week[ msg_week ] += 1

                if last_outgoing is not None and last_message == last_outgoing: # incoming message response
                    last_delta = (m.created - last_outgoing.created).total_seconds()
                    cutoff = 172800 # 43200 = 12h 21600 = 6h 172800 - 2days
                    if last_outgoing.is_system:
                        c.respond_system += 1
                        c.respond_system_2d += 1 if last_delta > cutoff else 0
                        reply_delta_system_total_seconds += last_delta
                        total_characters_system += len(m.text)
                        if last_outgoing.external_status == 'Success':
                            c.reply_delivered += 1
                            c.reply_delivered_2d += 1 if last_delta > cutoff else 0
                        elif last_outgoing.external_status == 'Sent':
                            c.reply_unkown += 1
                            c.reply_unkown_2d += 1 if last_delta > cutoff else 0
                        else:
                            c.reply_failed += 1
                            c.reply_failed_2d += 1 if last_delta > cutoff else 0

                        # Visit response totals
                        if 'visit' in last_outgoing.auto:
                            if 'pre' in last_outgoing.auto:
                                c.visit_pre_response += 1
                            elif 'missed' in last_outgoing.auto:
                                c.visit_miss_response += 1
                            elif 'attend' in last_outgoing.auto:
                                c.visit_attend_response += 1
                    else:
                        c.respond_nurse += 1
                        c.respond_nurse_2d += 1 if last_delta > cutoff else 0
                        reply_delta_nurse_total_seconds += last_delta
                        total_characters_nurse += len(m.text)
                else: # incoming message responding to incoming message
                    c.respond_none += 1
                    total_characters_none += len(m.text)
            last_message = m

        if current_miss_streak > c.miss_streak:
            c.miss_streak = current_miss_streak
        if current_streak > c.success_streak:
            c.success_streak = current_streak
        if current_sent_streak > c.sent_streak:
            c.sent_streak = current_sent_streak

        c.weeks_active = sum( 1 for i in msgs_per_week if i > 0 )
        c.weeks_active_anc = sum( 1 for i in msgs_per_week[:c.anc_weeks] if i > 0 )
        c.week_26_active = sum( 1 for i in msgs_per_week[:26] if i > 0)
        c.max_conversation = max( msgs_per_week )

        # TODO: split into nurse and system
        c.avg_msg_length = total_characters / c.msg_incoming if c.msg_incoming != 0 else 0
        c.avg_msg_length_system = total_characters_system/ c.respond_system if c.respond_system != 0 else 0
        c.avg_msg_length_nurse = total_characters_nurse / c.respond_nurse if c.respond_nurse != 0 else 0
        c.avg_msg_length_none = total_characters_none / c.respond_none if c.respond_none != 0 else 0

        # TODO: split into nurse and system
        c.avg_msg_delta = delivery_delta_total_hours / c.msg_outgoing if c.msg_outgoing != 0 else 0
        c.avg_msg_delta_system = delivery_delta_system_total_hours / c.msg_system if c.msg_system != 0 else 0
        c.avg_msg_delta_nurse = delivery_delta_nurse_total_hours / c.msg_nurse if c.msg_nurse != 0 else 0

        c.msgs_per_week = float(c.msg_incoming) / c.msg_weeks if c.msg_weeks != 0 else 0

        c.avg_reply = (reply_delta_system_total_seconds + reply_delta_nurse_total_seconds) / ((c.respond_system + c.respond_nurse) * 3600.0) if c.respond_system + c.respond_nurse > 0 else 0
        c.avg_reply_system = reply_delta_nurse_total_seconds / (c.respond_system * 3600.0) if c.respond_system > 0 else 0
        c.avg_reply_nurse = reply_delta_nurse_total_seconds / (c.respond_nurse * 3600.0) if c.respond_nurse > 0 else 0

        c.last_miss_streak = current_miss_streak

        c.percent_delivered = blank_or_percent( c.msg_delivered , c.msg_outgoing )
        c.success_system_percent = blank_or_percent( c.success_system, c.msg_system )
        c.success_nurse_percent = blank_or_percent( c.success_nurse, c.msg_nurse )

        c.reply_delivered_p = blank_or_percent( c.reply_delivered , c.msg_delivered )
        c.reply_unkown_p = blank_or_percent( c.reply_unkown , c.msg_sent )
        c.reply_failed_p = blank_or_percent( c.reply_failed , c.msg_other )

        for char , buckets in ( ('d',delivered_buckets) , ('n',not_delivered_buckets) ):
            for idx , count in enumerate(buckets):
                setattr(c,"%s%i"%(char,idx+1), blank_or_percent(count,bucket_sizes[idx]))

        for idx , window in enumerate([(0,26),(26,52),(52,78),(78,None)]):
            msgs = msgs_per_week[slice(window[0],window[1])]
            active = sum( 1 for i in msgs if i > 0)
            size = len(msgs)
            setattr(c,'a%i'%(idx+1), zero_or_percent(active,size))

    return contacts.values()

def external_delta(m):
    if m.external_success_time is not None:
        return (m.external_success_time - m.created).total_seconds()

def reply_time(m):
    next_participant = m.contact.message_set.filter(created__gt=m.created,is_outgoing=False).last()
    next_outgoing = m.contact.message_set.filter(created__gt=m.created,is_outgoing=True).last()
    if next_participant and next_outgoing and next_participant.created < next_outgoing.created:
        reply_time = (next_participant.created - m.created).total_seconds() / 3600
        m.next_outgoing = next_outgoing
        return reply_time
    return None

def replies(m):
    if hasattr(m,'next_outgoing'):
        replies = m.contact.message_set.filter(created__gt=m.created,created__lt=m.next_outgoing.created).count()
        return replies
    return None

system_message_columns = collections.OrderedDict([
    ('id','contact.study_id'),
    ('group','contact.study_group'),
    ('facility','contact.facility'),
    ('validated',lambda m: 1 if m.contact.is_validated else 0),
    ('since_enrollment', lambda obj: int((obj.created.date() - obj.contact.created.date()).total_seconds() / 86400) ),
    ('since_delivery', lambda obj: int((obj.created.date() - obj.contact.delivery_date).total_seconds() / 86400) if obj.contact.delivery_date is not None else '' ),
    ('status','contact.status'),
    ('timestamp','created'),
    ('sent_by','sent_by'),
    ('auto','auto'),
    ('external_status',lambda row: row.external_status if row.external_status in ('Success','Sent') else 'Failed'),
    ('external_delta', external_delta ),
    # ('reply_time',reply_time),
    # ('replies',replies),
])
system_message_columns.queryset = cont.Message.objects.filter(is_outgoing=True,contact__isnull=False)\
    .exclude(contact__study_group='control').select_related('contact').order_by('contact__study_group','contact')
system_message_columns.widths = {'E':25,'G':20}

def make_facility_worksheet(columns,ws,facility):
    contacts = cont.Contact.objects.filter(facility=facility)
    ws.title = facility.capitalize()
    make_worksheet(columns,ws,contacts)


def make_worksheet(columns,ws,queryset,freeze_panes='A2'):
    # Write Header Row
    ws.append(columns.keys())
    ws.auto_filter.ref = 'A1:{}1'.format( xl.utils.get_column_letter(len(columns)) )

    if hasattr(columns,'widths'):
        for col_letter, width in columns.widths.items():
            ws.column_dimensions[col_letter].width = width

    # Write Data Rows
    for row in queryset:
        ws.append( [make_column(row,attr) for attr in columns.values()] )

    ws.freeze_panes = freeze_panes

def make_weekly_wb():

    print "Making Weekly XLSX Report"

    wb = xl.Workbook()
    ws = wb.active

    week_start = timezone.make_aware(datetime.datetime(2015,11,22))
    today = timezone.make_aware( datetime.datetime( *datetime.date.today().timetuple()[:3] ) )
    ws.append( ('Start','End','Enrolled','System','Success','Participant','Nurse','Spam') )
    ws.freeze_panes = 'A2'
    while week_start < today:
        week_end = week_start + datetime.timedelta(days=7)
        messages = cont.Message.objects.filter(created__gte=week_start,created__lt=week_end)

        count = cont.Contact.objects.filter(created__lt=week_end).count()
        system = messages.filter(is_outgoing=True,is_system=True).count()
        success = messages.filter(is_outgoing=True,is_system=True,external_status='Success').count()
        nurse = messages.filter(is_outgoing=True,is_system=False).count()
        participant = messages.filter(is_outgoing=False,is_system=False,contact__isnull=False).count()
        spam = messages.filter(is_outgoing=False,is_system=False,contact__isnull=True).count()

        ws.append( (week_start.date(),week_end.date(),count,system,success,participant,nurse,spam) )

        week_start = week_end

    wb.save('ignore/weely_messages.xlsx')

def make_anonymous_wb(n=None):

    prefix_regx = re.compile('(rachuonyo| ahero| riruta| siaya| bondo| mathare)[ .]?', re.I)
    def anonomize_system(msg):
        text = msg.text
        match = prefix_regx.search(text)
        if match is not None:
            pos = match.end()
            return '{name}, this is {nurse} from {clinic}. ' + text[pos:]
        return text

    def anonomize_nurse(msg,display=False):
        text = msg.display_text if display is True else msg.text
        name_parts = msg.contact.nickname.lower().split()
        if name_parts[0] == 'min' or name_parts[0] == 'mama':
            # remove min and mama as names
            name_parts = name_parts[1:]
        for idx , w in enumerate(name_parts):
            text = re.sub(' %s(?= ?)' % w , ' {name}', text ,flags=re.I)
        text = re.sub(' ?({name} ?)+',' {name}',text)
        return text

    def delivery_weeks(msg):
        if msg.contact.delivery_date is not None:
            return (msg.created.date() - msg.contact.delivery_date).total_seconds() / 604800
        else:
            return (msg.created.date() - msg.contact.due_date).total_seconds() / 604800

    def enrollment_weeks(msg):
        return (msg.created - msg.contact.created).total_seconds() / 604800

    print "Making Anonymous Message XLSX Report"

    wb = xl.Workbook()
    ws = wb.active
    # Header Row
    header_row = ('anon_id','created','sent_by','chars','words','topic',
        'text','languages','related','delivered','original','weeks_delivery','weeks_enrollment')
    ws.append( header_row )
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = 'A1:{}1'.format( xl.utils.get_column_letter(len(header_row)) )

    # Set widths
    widths = {'B':20,'F':50,'K':50}
    for col_letter, width in widths.items():
        ws.column_dimensions[col_letter].width = width

    # Get Data
    messages = cont.Message.objects.filter(contact__study_group='two-way').order_by('contact__id','-created').prefetch_related('contact')

    contact = messages.first().contact

    for msg in messages[:n]:

        chars = len(msg.text)
        words = len(msg.text.split())

        if msg.is_outgoing is False:
            # Incoming message from participant
            data_row = (msg.contact.id, msg.created, msg.sent_by(), chars, words, msg.topic,
                msg.display_text, msg.languages, 1 if msg.is_related else 0, '', msg.text, delivery_weeks(msg) , enrollment_weeks(msg),
            )
        elif msg.is_system is False:
            # Outgoing message from nurse
            data_row = (msg.contact.id, msg.created, msg.sent_by(), chars, words, '',
                anonomize_nurse(msg,display=True), msg.languages, '', msg.external_status, anonomize_nurse(msg), delivery_weeks(msg) , enrollment_weeks(msg),
            )
        else:
            # System message
            data_row = (msg.contact.id, msg.created, msg.sent_by(), chars, words, '',
                msg.display_text, msg.contact.language,'', msg.external_status, anonomize_system(msg), delivery_weeks(msg), enrollment_weeks(msg),
            )
            # ws.append( (msg.contact.study_id,msg.display_text,'system',msg.text) )
        ws.append( data_row )


    wb.save('ignore/mx_anonymoized.xlsx')

def make_message_wb(mode='s'):

    print "Making Message XLSX Report"
    wb = xl.Workbook()
    ws = wb.active

    if mode.startswith('a'):
        # Make two_way, one_way, and control sheets
        print " - Making Two-Way Sheet "
        ws.title = 'two-way'
        make_message_ws(ws,cont.Contact.objects.filter(study_group='two-way'))
        print " - Making One-Way Sheet "
        ws = wb.create_sheet(title='one-way')
        make_message_ws(ws,cont.Contact.objects.filter(study_group='one-way'))
        print " - Making Control Sheet "
        ws = wb.create_sheet(title='control')
        make_message_ws(ws,cont.Contact.objects.filter(study_group='control'))
    elif mode.startswith('f'): # full two-way
        make_message_ws(ws,cont.Contact.objects.filter(study_group='two-way'))
    elif mode.startswith('m'): #meta
        make_message_meta_ws(ws)
    else:
        make_message_ws(ws,cont.Contact.objects.filter(study_id__in=('0003','0803')))

    wb.save('ignore/messages_export.xlsx')

def make_message_ws(ws,queryset):

    header =  ('mid','pid','day','created','auto','external','delta_human','delta','delta_last',
               'study_wk','edd_wk','chars','words','topic','related',
               'sent_by','language','original','english')
    widths = {'C':5,'D':20,'E':25,'H':12,'I':12,'J':12,'M':20,'N':20}
    xl_add_header_row(ws,header,widths)

    def date_day(datetime):
        return (datetime.strftime('%a') , datetime)

    for p in queryset.all():
        previous  = Namespace(participant=None)
        p_cols = (p.study_id,)
        for m in p.message_set.prefetch_related('contact').order_by('created'):
            study_wk , edd_wk = m.study_wk , m.edd_wk
            if m.is_system:
                previous.system , previous.out = m , m
                auto = m.get_auto()
                ws.append( (m.id,) + p_cols + date_day(m.created) + (m.auto, m.external_status,'','','',
                          study_wk, edd_wk, len(m.text), len(m.text.split()), auto.comment if auto else '', '',
                          m.sent_by(),p.language,m.text,m.translated_text,
                ) )
                xl_style_current_row(ws)
            else:
                if m.is_outgoing is True: # Nurse message
                    delta = m.created - (previous.participant.created if previous.participant is not None else m.contact.created)
                    previous.out = m
                    ws.append( (m.id,) + p_cols + date_day(m.created) + ( '',
                              m.external_status,seconds_as_str(delta,True),delta.total_seconds(),'',study_wk,edd_wk,
                              len(m.text),len(m.text.split()), '', '',
                              m.sent_by(),m.languages,m.text,m.translated_text,
                    ) )
                    ws["E{0}".format(ws._current_row)].font = bold_font
                else: # Participant message
                    previous.participant = m
                    delta = m.created - previous.system.created
                    delta_last = '' if previous.out == previous.system else (m.created - previous.out.created).total_seconds()
                    ws.append( (m.id,) + p_cols + date_day(m.created) + ( '',
                        '', seconds_as_str(delta,True),delta.total_seconds(),delta_last,
                        study_wk,edd_wk, len(m.text),len(m.text.split()), m.topic, m.is_related,
                         m.sent_by(),m.languages,m.text,m.translated_text,
                    ) )

def make_message_meta_ws(ws):

    header =  ('id','group','sims','conn','sent_by','day','timestamp','delivery_delta','status', 'reason',
                'auto','short', 'study_wk','delivery_wk', 'response_delta','response_system',
                'chars','words','topic','related', 'language'
            )
    widths = {'F':5,'G':20,'J':20,'K':20,'S':20}
    xl_add_header_row(ws,header,widths)

    def date_day(datetime):
        return datetime.strftime('%a')

    conn_map = {}
    auto_memory = {}
    sim_map = {v['id']:v['sims'] for v in cont.Contact.objects_no_link.annotate(sims=models.Count('connection')).values('id','sims')}
    previous  = Namespace()
    messages = cont.Message.objects.filter(contact__study_group__endswith='way')\
        .order_by('contact__study_group','contact__study_id','created')\
        .prefetch_related('contact','parent')
    # messages = messages.filter(contact__study_id__in=('0003','0008'))
    for m in messages.all():
        response_delta , response_delta_system = '' , ''
        languages = m.languages
        if m.is_system is True:
            previous.system, previous.out = m , m
            languages = m.contact.language
            status = m.external_status
            if m.auto not in auto_memory:
                auto_memory[m.auto] = m.get_auto()
            auto = auto_memory[m.auto]
            m.topic = auto.comment if auto else ''
        elif m.is_outgoing is True: # Nurse Message
            previous.out = m
            status = m.external_status
            response_delta = (m.created - m.parent.created).total_seconds() / 3600 if m.parent else ''
        else: # Participant message
            response_delta_system = (m.created - previous.system.created).total_seconds() / 3600 if previous.system != previous.out else ''
            response_delta = (m.created - previous.out.created).total_seconds() / 3600
            status = 'Received'

        ws.append( (
            m.contact.study_id, m.contact.study_group,
            sim_map.get(m.contact_id), conn_map.setdefault(m.connection_id,len(conn_map)),
            m.sent_by(), date_day(m.created), m.created,
            m.delivery_delta, m.external_status, m.reason, m.auto, m.auto_type, m.study_wk , m.delivery_wk,
            response_delta, response_delta_system, len(m.text), len(m.text.split()), m.topic, m.is_related, languages
        ) )

    def get_cell_value(ws,col,row):
        return ws['%s%i'%(col,row)].value

    previous.participant_sent = None
    for ridx in range(ws.max_row,1,-1):
        if get_cell_value(ws,'C',ridx) == 'participant':
            previous.participant_sent = get_cell_value(ws,'E',ridx)
        elif get_cell_value(ws,'C',ridx) == 'system':
            if previous.participant_sent is not None:
                delta = (previous.participant_sent - get_cell_value(ws,'E',ridx)).total_seconds() / 3600
                ws['M%i'%ridx] = delta
            previous.participant_sent = None

def make_miss_streak_count_wb():

    print "Making Miss Streak XLSX Report"

    wb = xl.Workbook()
    ws = wb.active

    header  =  ('id','group','sims','week','p_success','p_fail','p_pct','miss_count','a_success','a_fail','a_pct')
    widths = {'H':15}
    xl_add_header_row(ws,header,widths)

    contacts = cont.Contact.objects_no_link.exclude(study_group='control').annotate(
        total_success=utils.sql_count_when(message__is_system=True,message__external_status='Success'),
        total_fail=utils.sql_count_when(~models.Q(message__external_status='Success'),message__is_system=True)
    ).order_by('study_group','study_id')

    # contacts = contacts.filter(study_id__in=['0001','0004','0005'])
    for c in contacts:
        current_miss_streak , prior_success, prior_fail = 0 , 0 , 0
        # TODO: Filter out visit messages
        for m in c.message_set.filter(is_system=True).order_by('created'):
            if m.external_status != 'Success':
                prior_fail += 1
                current_miss_streak += 1
            else:
                if current_miss_streak > 0:
                    prior_total = prior_success + prior_fail - current_miss_streak
                    after_total = c.total_success - prior_success + c.total_fail - prior_fail
                    ws.append( (c.study_id, c.study_group, c.sim_count, int(m.study_wk),
                        prior_success, prior_fail - current_miss_streak, zero_or_percent(prior_success , prior_total),
                        current_miss_streak,
                         c.total_success - prior_success , c.total_fail - prior_fail, zero_or_percent(c.total_success - prior_success , after_total)
                    ) )
                    ws["H{0}".format(ws._current_row)].font = bold_font
                prior_success += 1
                current_miss_streak = 0
        if current_miss_streak > 0:
            ws.append( (c.study_id, c.study_group, c.sim_count, int(m.study_wk),
                prior_success, prior_fail - current_miss_streak, zero_or_percent(prior_success , prior_total),
                current_miss_streak,
                 c.total_success - prior_success , c.total_fail - prior_fail, zero_or_percent(c.total_success - prior_success , after_total)
            ) )
            ws["H{0}".format(ws._current_row)].font = bold_font
    wb.save('ignore/msg_streaks.xlsx')

def make_conversations_wb():
    """ Create a report of all conversations from system messages """

    print "Making Conversations XLSX Report"
    wb = xl.Workbook()
    ws = wb.active
    header =  ('id','sent','auto','short','topic','status','delivery_delta','response_delta',
                'participant','nurse','total','p_topic','% on topic','order',)
    widths = {'B':20,'C':28,'D':20,'E':25,'L':30}
    xl_add_header_row(ws,header,widths)

    auto_memory = {}

    cur_system , first_response , p_topic = None , None , None
    counts, order =  collections.defaultdict(int) , []
    two_way = cont.Contact.objects.filter(study_group='two-way').prefetch_related('message_set')
    # for p in two_way.filter(study_id__in=('0003','0803')):
    for p in two_way.all():
        for msg in p.message_set.all().order_by('created'):
            if msg.is_system is True:
                if cur_system is not None:
                    if cur_system.auto not in auto_memory:
                        auto_memory[cur_system.auto] = cur_system.get_auto()
                    auto = auto_memory[cur_system.auto]
                    delivery_delta = (cur_system.external_success_time - cur_system.created).total_seconds() / 3600.0 if cur_system.external_success_time else ''
                    if first_response is not None:
                        response_delta = (first_response.created - cur_system.created).total_seconds() / 3600.0
                        p_topic = first_response.topic
                    else:
                        response_delta, p_topic = '', ''
                    if cur_system.external_status not in ('Success','Sent',''):
                        order = cur_system.reason
                    else:
                        order = ','.join(order)
                    # Append Conversation Row for System Message
                    ws.append(( p.study_id, cur_system.created, cur_system.auto, cur_system.auto_type, auto.comment if auto else '',
                                cur_system.external_status, delivery_delta, response_delta,
                                counts['in'], counts['nurse'], counts['total'],
                                p_topic, float(counts['topic']) / counts['in'] if counts['in'] > 0 else 0, order
                            ))
                cur_system , first_response = msg , None
                counts, order =  collections.defaultdict(int) , []
            elif msg.is_outgoing is True: # Non System Outgoing Message
                counts['nurse'] += 1
                order.append('n')
            else: # incomming message
                if first_response is None:
                    first_response = msg
                counts['in'] += 1
                counts['topic'] += 1 if msg.topic == first_response.topic else 0
                order.append('p')
            counts['total'] += 1
        # Print last row
        if cur_system is not None:
            if cur_system.auto not in auto_memory:
                auto_memory[cur_system.auto] = cur_system.get_auto()
            auto = auto_memory[cur_system.auto]
            delivery_delta = (cur_system.external_success_time - cur_system.created).total_seconds() / 3600.0 if cur_system.external_success_time else ''
            if first_response is not None:
                response_delta = (first_response.created - cur_system.created).total_seconds() / 3600.0
                p_topic = first_response.topic
            else:
                response_delta, p_topic = '', ''
            if cur_system.external_status not in ('Success','Sent',''):
                order = cur_system.reason
            else:
                order = ','.join(order)
            ws.append(( p.study_id, cur_system.created, cur_system.auto, cur_system.auto_type, auto.comment if auto else '',
                        cur_system.external_status, delivery_delta, response_delta,
                        counts['in'], counts['nurse'], counts['total'],
                        p_topic, float(counts['topic']) / counts['in'] if counts['in'] > 0 else 0, order
                    ))
        cur_system , first_response = None , None
        counts, order =  collections.defaultdict(int) , []

    wb.save('ignore/conversations.xlsx')


def null_boolean_factory(attribute):

    def null_boolean(obj):
        value = getattr(obj,attribute)
        if value is None:
            return 99
        if value is True:
            return 1
        return 0

    return null_boolean

def make_csv(columns,data,file_path):
    ''' Write data to {file_path}.csv '''

    with open( file_path , 'wb') as csvfile:
        csv_writer = csv.writer(csvfile)

        # Header Row
        csv_writer.writerow( columns.keys() )
        for row in data:
            csv_writer.writerow( [ make_column(row,value) for value in columns.values()] )

########################################
#SEC::Utility Functions
########################################

def seconds_as_str(seconds,as_min=False):
    if seconds is None:
        return None
    if isinstance(seconds,datetime.timedelta):
        seconds = seconds.total_seconds()
    if as_min is False:
        if seconds <= 3600:
            return '{:.2f}'.format(seconds/60)
        return '{:.2f} (h)'.format(seconds/3600)
    else:
        days , hours = divmod(seconds, 86400)
        hours , mins = divmod(hours, 3600)
        mins , secons = divmod(mins,60)
        outstr = ''
        if days != 0:
            outstr += '{:.0f}d '.format(days)
        if hours != 0:
            outstr += '{:.0f}h '.format(hours)
        if mins != 0:
            outstr += '{:.0f}m '.format(mins)
        return outstr

def delta_days(date,past=False):
    if date is not None:
        days = (date - datetime.date.today()).days
        return -days if past else days

def blank_or_percent(frac,total):
    return zero_or_percent(frac,total,'')

def zero_or_percent(frac,total,zero=0):
    if total == 0:
        return zero
    return round( float(frac) / total , 3 )
########################################
# Message Row Counting Classes for print stats
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
        """ Iterate over values in column order instead of keys """
        for c in self.columns:
            yield self[c]

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
        return "{:^12}{:^18}{:^18}{:^18}{:^18}{:^18}{:^18}{:^18}".format(
            "","Pregnant","Post-Partum","SAE OptIn","SAE OptOut","Withdrew","Other","Total"
        )

    def row_str(self,label):
        str_fmt = "{0:^12}{1[pregnant].condensed:^18}{1[post].condensed:^18}{1[loss].condensed:^18}"
        str_fmt += "{1[sae].condensed:^18}{1[stopped].condensed:^18}{1[other].condensed:^18}{2:^18}"
        return str_fmt.format( label , self, self.total().condensed_str() )

class MessageTypeRow(CountRowBase):

    columns = ['edd','dd','loss','visit','bounce','stop','signup',
                'control','one-way','two-way','nurse','anonymous','empty_auto']

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

########################################
# Report Utilities
########################################

def message_status_groups(start=None,delta='day'):
    """ Create report of message status for nightly email """

    if delta not in ('day','week','cur_week','month','year','all'):
        delta = 'day'


    if start is None:
        start = datetime.date.today() - datetime.timedelta(days=1)
    start = utils.make_date( start ) # Make timezone aware
    if delta == 'day':
        end = start + datetime.timedelta(days=1)
    elif delta == 'week':
        start = start - datetime.timedelta(days=start.weekday()) # Get start of week
        end = start + datetime.timedelta(weeks=1)
    elif delta == 'cur_week':
        end = start
        start = end - datetime.timedelta(weeks=1)
    elif delta == 'month':
        start = start.replace(day=1) # Get start of month
        # Get last day of month
        day_in_next_month = start.replace(day=28) + datetime.timedelta(days=4)
        first_day_next_month = day_in_next_month.replace(day=1)
        last_day_in_month = first_day_next_month - dtatetime.timedelta(days=1)
        end = start.replace(day=last_day_in_month.day)
    elif delta == 'year':
        start = start.replace(month=1,day=1)
        end = start.replace(month=12,day=31)
    elif delta == 'all':
        end = start
        start = utils.make_date(2010,1,1)

    out_string = ['Message Success Stats From: {} To: {}'.format(start.strftime('%Y-%m-%d'),end.strftime('%Y-%m-%d')), '']

    messages = cont.Message.objects.filter(created__range=(start,end))
    msg_groups = messages.order_by().values(
        'external_status','contact__study_group'
    ).annotate(
        count=models.Count('external_status'),
    )

    # Create OrderedDict for Groups
    status_counts = [('Success',0),('Sent',0),('Failed',0),('Other',0),('',0),('Total',0)]
    msg_dict = collections.OrderedDict( [
        ('two-way',collections.OrderedDict( status_counts ) ),
        ('one-way',collections.OrderedDict( status_counts ) ),
        ('control',collections.OrderedDict( status_counts ) ),
        (None,collections.OrderedDict( status_counts ) )
    ] )

    for group in msg_groups:
        group_dict = msg_dict[group['contact__study_group']]
        try:
            group_dict[group['external_status']] += group['count']
        except KeyError as e:
            group_dict['Other'] += group['count']
        group_dict['Total'] += group['count']

    out_string.append( '{:^15}{:^10}{:^10}{:^10}{:^10}{:^10}{:^10}'.format(
        'Group','Delivered','Sent','Failed','Other','Sent','Total') )
    total_row = collections.OrderedDict( status_counts )
    for group , status_dict in msg_dict.items():
        out_string.append( '{:^15}{:^10}{:^10}{:^10}{:^10}{:^10}{:^10}'.format(
            group, *status_dict.values()
        ) )
        for key in ['Success','Sent','','Other','Total','Failed']:
            total_row[key] += status_dict[key]

    out_string.append( '{:^15}{:^10}{:^10}{:^10}{:^10}{:^10}{:^10}'.format(
        'Total', *total_row.values()
    ) )
    total_messages = float(sum(total_row.values())/2)
    if total_messages == 0:
        total_percents = [0 for _ in range(len(total_row))]
    else:
        total_percents = [ c*100/total_messages for c in total_row.values() ]
    out_string.append( '{:^15}  {:06.3f}    {:06.3f}    {:06.3f}    {:06.3f}    {:06.3f}    {:06.3f}'.format(
        '%', *total_percents
    ) )
    out_string.append('')

    return '\n'.join(out_string)
