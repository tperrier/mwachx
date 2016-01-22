#!/usr/bin/python
from optparse import make_option
import datetime, openpyxl as xl
import sys

from django.core.management.base import BaseCommand
from django.utils import dateparse
from django.db import models


import contacts.models as cont
import backend.models as back
from transports.email import email


class Command(BaseCommand):

    help = 'send daily sms messages'

    def add_arguments(self,parser):
        parser.add_argument('-s','--send',help='flag to send messages default (False)',action='store_true',default=False)
        parser.add_argument('--date',help='set testing date')
        parser.add_argument('-t','--hour',help='set testing hour',choices=(0,8,13,20),type=int)
        parser.add_argument('-d','--day',help='set testing day',choices=range(7),type=int)
        parser.add_argument('-e','--email',help='send output as email',action='store_true',default=False)
        parser.add_argument('--test',help='test send_messages can be called',action='store_true',default=False)

    def handle(self,*args,**options):
        if options.get('test'):
            self.stdout.write( 'Time: {}\nVersion: {}\nPath: {}\n'.format(datetime.datetime.now(),sys.version,sys.path) )
            return

        day = options.get('day')
        hour = options.get('hour')
        date = options.get('date')

        if day is None:
            try:
                date = datetime.datetime.strptime(date if date is not None else '','%Y-%m-%d').date()
            except ValueError as e:
                # Invlaid date object so set to today
                date = datetime.date.today()
            day = date.weekday()

        if hour is None:
            hour = datetime.datetime.now().hour
        hour = [0,8,8,8,8,  8,8,8,8,8, 8,13,13,13,13, 13,20,20,20,20, 20,20,20,20][hour]
        day_lookup = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']

        # self.stdout.write("Finding Participants for Day: {} Hour: {}".format(day_lookup[day],hour))

        participants = cont.Contact.objects.filter(send_day=day,status__in=['pregnant','post','over','ccc'])
        if hour != 0:
            participants = participants.filter(send_time=hour)

        total_counts = dict( participants.values_list('study_group').annotate(models.Count('study_group')) )
        for key in ('control','one-way','two-way'):
            if key not in total_counts:
                total_counts[key] = 0

        total_string = "Found {total} total participants. Control: {dict[control]} One-Way: {dict[one-way]} Two-Way: {dict[two-way]}"\
            .format(total=sum(total_counts.values()),dict=total_counts)

        participants = participants.exclude(study_group='control')
        no_messages = []
        for p in participants:
            message = p.send_automated_message(today=date,send=options.get('send'))
            if message is None:
                no_messages.append( '{} (#{})'.format( p.description(today=date),p.study_id)  )

        out_message = total_string+"\n\n"
        out_message += "Messages not sent: {}".format(len(no_messages))
        out_message += "\n\t{}\n".format('\n\t'.join(no_messages))

        subject = '{}Sending {} {}h00 ({})'.format(
            'Fake ' if not options.get('send') else '',
            day_lookup[day],hour,
            sum(total_counts.values())
        )


        if options.get('email'):
            email(subject,out_message)
        else:
            self.stdout.write(subject)
            self.stdout.write(out_message)
