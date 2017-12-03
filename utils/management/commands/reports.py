#!/usr/bin/python
 # -*- coding: utf-8 -*-
import datetime, openpyxl as xl, os
import code
import operator, collections
import unicodecsv as csv

from django.core.management.base import BaseCommand, CommandError
from django.db import models
from django.utils import timezone

import backend.models as back
import contacts.models as cont
import utils
import report_utils

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
        print_parser.add_argument('--weeks',default=5,type=int,help='message history weeks (default 5)')
        print_parser.set_defaults(action='print_stats')

        xlsx_parser = subparsers.add_parser('xlsx',cmd=parser.cmd,help='create xlsx reports')
        xlsx_parser.add_argument('-t','--visit',action='store_true',default=False,help='create visit report')
        xlsx_parser.add_argument('-d','--detail',action='store_true',default=False,help='create detail report')
        xlsx_parser.add_argument('-a','--all',action='store_true',default=False,help='create all reports')
        xlsx_parser.add_argument('-i','--interaction',action='store_true',default=False,help='create participant interaction report')
        xlsx_parser.add_argument('-m','--messages',action='store_true',default=False,help='create system message dump')
        xlsx_parser.add_argument('-w','--weekly',action='store_true',default=False,help='create weakly stats report')
        xlsx_parser.add_argument('-c','--custom',action='store_true',default=False,help='create custom report')
        xlsx_parser.add_argument('--dir',default='ignore',help='directory to save report in')
        xlsx_parser.set_defaults(action='make_xlsx')

        csv_parser = subparsers.add_parser('csv',cmd=parser.cmd,help='create csv reports')
        csv_parser.add_argument('--dir',default='ignore',help='directory to save csv in')
        csv_parser.add_argument('name',help='csv report type',
            choices=(
                'hiv_messaging','enrollment','messages','edd','delivery',
                'sae','visits','msg_dump','hiv_statuschange','participant_dump',
            )
        )
        csv_parser.set_defaults(action='make_csv_name')

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
        if self.options['topics']:
            self.print_report('msg_topics')
        if self.options['msg_counts']:
            self.print_report('msg_counts')
        if self.options['message_status'] is not None:
            self.print_message_status()
        if self.options['success_times']:
            self.print_success_times()

    def print_report(self,report):
        report_modual = getattr(report_utils,report)
        report_modual.print_report(self)

    # SEC::XLSX Helper Functions
    def make_xlsx(self):

        workbook_columns = {}
        if self.options['visit'] or self.options['all']:
            workbook_columns['visit'] =  visit_columns
        if self.options['detail'] or self.options['all']:
            workbook_columns['detail'] =  detail_columns
        if self.options['custom']:
            workbook_columns['custom'] =  detail_columns
        if self.options['interaction']:
            workbook_columns['interaction'] =  interaction_columns
            interaction_columns.queryset = make_interaction_columns()
        if self.options['messages']:
            workbook_columns['messages'] = system_message_columns
            # system_message_columns.queryset = make_system_message_columns()
        if self.options['weekly']:
            make_weekly_wb()

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

        # # Print Group Counts
        # self.stdout.write( "{:^12}{:^12}{:^12}{:^12}{:^12}".format("","Control","One-Way","Two-Way","Total") )
        # total_row = LanguageRow()
        # for facility, row in language_counts.items():
        #     self.stdout.write( "{0:^12}{1[control]:^12}{1[one-way]:^12}{1[two-way]:^12}{2:^12}".format(
        #         facility.capitalize(), row, row.total()
        #     ) )
        #     total_row += row
        #
        # self.stdout.write( "{0:^12}{1[control]:^12}{1[one-way]:^12}{1[two-way]:^12} {2:^12}".format(
        #     "Total", total_row, total_row.total()
        # ) )
        #
        # print ''
        self.print_header('Language of Messages (participant,nurse)')

        message_groups = cont.Message.objects.order_by().filter(contact__study_group='two-way',is_system=False)\
            .prefetch_related('contact').values('languages','contact__language','is_outgoing')\
            .exclude(languages='').annotate(count=models.Count('id',distinct=True))

        # Piviot Group Counts
        language_counts = collections.defaultdict(LanguageMessageRow)
        for g in message_groups:
            language_str = ','.join( set( s[0] if s!= 'sheng' else 'h' for s in g['languages'].split(';') ) )
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
            ('scheduled','scheduled'),
            ('status','status'),
            ('arrived','arrived'),
            ('sms_count','missed_sms_count'),
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
        columns = collections.OrderedDict([
            ('timestamp','created'),
            ('study_id','contact.study_id'),
            ('facility','contact.facility'),
            ('since_enrollment', lambda obj: int((obj.created.date() - obj.contact.created.date()).total_seconds() / 86400) ),
            ('since_delivery', lambda obj: int((obj.created.date() - obj.contact.delivery_date).total_seconds() / 86400) if obj.contact.delivery_date is not None else '' ),
            ('topic','topic'),
            ('related','is_related'),
            ('languages','languages'),
            ('text','display_text'),
            ('chars',lambda m: len(m.text)),
            ('words',lambda m: len( m.text.split() )),
            ('text_raw','text'),
        ])
        m_all = cont.Message.objects.filter(is_outgoing=False,contact__study_group='two-way') \
            .order_by('contact__study_id').prefetch_related('contact')
        file_path = os.path.join(self.options['dir'],'message_dump.csv')
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
    ('group','study_group'),
    ('facility','facility'),
    ('status','status'),
    ('weeks','msg_weeks'),

    ('p_d','precent_delivered'),
    ('p_s','precent_sent'),
    ('p_f','precent_other'),

    ('success_system','system_success'),
    ('success_nurse','nurse_success'),
    ('ss_p','system_success_percent'),
    ('sn_p','nurse_success_percent'),

    ('reply_d','reply_delivered'),
    ('reply_s','reply_sent'),
    ('reply_f','reply_failed'),

    ('outgoing','msg_outgoing'),
    ('system','msg_system'),
    ('nurse','msg_nurse'),
    ('incoming','msg_incoming'),
    ('delivered','msg_delivered'),
    ('sent','msg_sent'),
    ('failed','msg_other'),

    ('streak_success','success_streak'),
    ('streak_sent','sent_streak'),
    ('streak_missed','miss_streak'),
    ('streak_start','start_streak'),
    ('streak_last','last_miss_streak'),

    ] + [ ("%s%i"%(c,i),"%s%i"%(c,i)) for c in ('d','s','f') for i in range(1,BUCKETS+1) ]
)

def make_interaction_columns():

    contacts = { c.id:c for c in
        cont.Contact.objects_no_link.annotate_messages().filter(msg_outgoing__gt=9)
        # cont.Contact.objects_no_link.filter(study_group='two-way').annotate_messages().order_by('-msg_failed')[:20]
    }

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
        start_streak, start_streak_flag = 0 , False
        success_streak ,  current_streak = 0 , 0
        sent_streak, current_sent_streak = 0 , 0
        miss_streak , current_miss_streak = 0 , 0
        system_success , nurse_success , = 0 , 0
        reply_delivered , reply_sent , reply_failed = 0 , 0 , 0

        # Set up bucket sizes based on how many system messages there are
        size , rem = divmod( c.msg_system , BUCKETS )
        bucket_sizes = [ (size+1) for i in range(rem) ] + [size for i in range(BUCKETS-rem)]
        delivered_buckets = [ 0 for _ in range(BUCKETS)]
        sent_buckets = [ 0 for _ in range(BUCKETS)]
        failed_buckets = [ 0 for _ in range(BUCKETS)]
        count , bucket = 0 , 0

        last_outgoing = None

        for m in c.messages:

            if m.is_outgoing:
                last_outgoing = m

                # Start Streak
                if not start_streak_flag:
                    if m.external_status == 'Success':
                        start_streak += 1
                    else:
                        start_streak_flag = True

                if m.external_status == 'Success':
                    current_streak += 1
                    if m.is_system:
                        system_success += 1
                    elif m.translation_status != 'cust':
                        nurse_success += 1
                    if current_miss_streak > miss_streak:
                        miss_streak = current_miss_streak
                    current_miss_streak = 0
                else:
                    current_miss_streak += 1
                    if current_streak > success_streak:
                        success_streak = current_streak
                    current_streak = 0

                if m.external_status == 'Sent':
                    current_sent_streak += 1
                else:
                    if current_sent_streak > sent_streak:
                        sent_streak = current_sent_streak
                    current_sent_streak = 0

                if m.is_system:
                    if count == bucket_sizes[bucket]:
                        # increment bucket if bucket is full
                        bucket += 1
                        count = 0
                    count += 1
                    if m.external_status == 'Success':
                        delivered_buckets[bucket] += 1
                    elif m.external_status == 'Sent':
                        sent_buckets[bucket] += 1
                    else:
                        failed_buckets[bucket] += 1

            elif last_outgoing is not None: # incoming message and no reply yet
                if (m.created - last_outgoing.created).total_seconds() < 172800: # 43200 = 12h 21600 = 6h
                    if last_outgoing.external_status == 'Success':
                        reply_delivered += 1
                    elif last_outgoing.external_status == 'Sent':
                        reply_sent += 1
                    else:
                        reply_failed += 1
                last_outgoing = None

        if current_miss_streak > miss_streak:
            miss_streak = current_miss_streak
        if current_streak > success_streak:
            success_streak = current_streak
        if current_sent_streak > sent_streak:
            sent_streak = current_sent_streak

        c.start_streak = start_streak
        c.success_streak = success_streak
        c.miss_streak = miss_streak
        c.sent_streak = sent_streak
        c.last_miss_streak = current_miss_streak

        c.precent_delivered = zero_or_precent( c.msg_delivered , c.msg_outgoing )
        c.precent_sent = zero_or_precent( c.msg_sent , c.msg_outgoing )
        c.precent_other = zero_or_precent( c.msg_other , c.msg_outgoing )

        c.system_success = system_success
        c.nurse_success = nurse_success
        c.system_success_percent = zero_or_precent( system_success , c.msg_system )
        c.nurse_success_percent = zero_or_precent( nurse_success , c.msg_nurse )

        c.reply_delivered = zero_or_precent( reply_delivered , c.msg_delivered )
        c.reply_sent = zero_or_precent( reply_sent , c.msg_sent )
        c.reply_failed = zero_or_precent( reply_failed , c.msg_other )

        c.msg_weeks = (c.messages[-1].created - c.messages[0].created).total_seconds() / (3600*24*7)

        for char , buckets in ( ('d',delivered_buckets) , ('s',sent_buckets) , ('f',failed_buckets) ):
            for idx , count in enumerate(buckets):
                setattr(c,"%s%i"%(char,idx+1), zero_or_precent(count,bucket_sizes[idx]))

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
    ('validated','contact.is_validated'),
    ('since_enrollment', lambda obj: int((obj.created.date() - obj.contact.created.date()).total_seconds() / 86400) ),
    ('since_delivery', lambda obj: int((obj.created.date() - obj.contact.delivery_date).total_seconds() / 86400) if obj.contact.delivery_date is not None else '' ),
    ('status','contact.status'),
    ('timestamp','created'),
    ('sent_by','sent_by'),
    ('auto','auto'),
    ('external_status',lambda row: row.external_status if row.external_status in ('Success','Sent') else 'Failed'),
    ('external_delta', external_delta ),
    ('reply_time',reply_time),
    ('replies',replies),
])
system_message_columns.queryset = cont.Message.objects.filter(is_outgoing=True,contact__isnull=False)\
    .exclude(contact__study_group='control').select_related('contact').order_by('contact__study_group','contact')
system_message_columns.widths = {'E':25,'G':20}

def make_facility_worksheet(columns,ws,facility):
    contacts = cont.Contact.objects.filter(facility=facility)
    ws.title = facility.capitalize()
    make_worksheet(columns,ws,contacts)


def make_worksheet(columns,ws,queryset):
    # Write Header Row
    ws.append(columns.keys())
    ws.auto_filter.ref = 'A1:{}1'.format( xl.utils.get_column_letter(len(columns)) )

    if hasattr(columns,'widths'):
        for col_letter, width in columns.widths.items():
            ws.column_dimensions[col_letter].width = width

    # Write Data Rows
    for row in queryset:
        ws.append( [make_column(row,attr) for attr in columns.values()] )

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
        for name in column.split('.'):
            obj = getattr(obj,name)
        return obj() if hasattr(obj,'__call__') else obj
    # Else assume column is a function that takes the object
    return column(obj)

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

def zero_or_precent(frac,total):
    if total == 0:
        return ''
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
        total_precents = [0 for _ in range(len(total_row))]
    else:
        total_precents = [ c*100/total_messages for c in total_row.values() ]
    out_string.append( '{:^15}  {:06.3f}    {:06.3f}    {:06.3f}    {:06.3f}    {:06.3f}    {:06.3f}'.format(
        '%', *total_precents
    ) )
    out_string.append('')

    return '\n'.join(out_string)
