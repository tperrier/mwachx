#!/usr/bin/python
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
        parser.add_argument('--date',default='',help='set testing date y-m-d')
        parser.add_argument('-t','--hour',help='set testing hour. use 0 for all',choices=(0,8,13,20),type=int)
        parser.add_argument('-d','--day',help='set testing day',choices=range(7),type=int)
        parser.add_argument('-e','--email',help='send output as email',action='store_true',default=False)
        parser.add_argument('--test',help='test send_messages can be called',action='store_true',default=False)
        # Can't have -v as a paramater since it conflicts with verbos   e
        parser.add_argument('-w','--weekly',help='send weekly messages',action='store_true',default=False)
        parser.add_argument('-a','--appointment',help='send visit appointment reminders as well',action='store_true',default=False)

    def handle(self,*args,**options):
        if options.get('test'):
            self.stdout.write( 'Time: {}\nVersion: {}\nPath: {}\n'.format(datetime.datetime.now(),sys.version,sys.path) )
            self.stdout.write( str(options) )
            return

        # Check for required arguments
        required = ['weekly','appointment']
        for key,value in options.items():
            if key in required and value == True:
                break
        else:
            raise ValueError( "No required argument found. {}".format(required) )

        # Try to parse the date option or use current date
        date = options.get('date')
        try:
            date = datetime.datetime.strptime(date,'%Y-%m-%d').date()
        except ValueError as e:
            # Invlaid date object so set to today
            date = datetime.date.today()

        # Parse weekday or use selected date
        day = options.get('day')
        if day is None:
            day = date.weekday()

        # Parse hour or use selected time
        hour = options.get('hour')
        if hour is None:
            hour = datetime.datetime.now().hour

        send = options.get('send')
        email_subject = '[MX Server] {}{}'.format( date.strftime('%a %b %d (%j) %Y'), '' if options.get('send') else ' (FAKE)' )
        email_body = [ "Script started at {}".format(datetime.datetime.now()),
                        "Options: {} D:{} H:{} Send:{}".format(date,day,hour,send), '' ]

        if options["weekly"]:
            weekly_messages(day,hour,date,email_body,send=send)
        if options["appointment"]:
            appointment_reminders(date,hour,email_body,send=send)


        email_body = '\n'.join(email_body)
        if options.get('email'):
            email(email_subject,email_body)
        else:
            self.stdout.write(email_subject)
            self.stdout.write(email_body)

def weekly_messages(day,hour,date,email_body,send=False):
    ''' Send weeky messages to participants based on day of week and time of day
        :param day(int): day of week to select participants for
        :param hour(int): hour of day (0 for all)
        :email_body(array): array of strings for email body
    '''

    email_body.append("***** Weekly Messages ******\n")

    participants = cont.Contact.objects.filter(send_day=day,status__in=['pregnant','post','over','ccc'])

    # Convert hour to 8,13 or 20
    hour = [0,8,8,8,8,  8,8,8,8,8, 8,13,13,13,13, 13,20,20,20,20, 20,20,20,20][hour]

    # Filter based on hour if needed
    if hour != 0:
        participants = participants.filter(send_time=hour)

    total_counts = dict( participants.values_list('study_group').annotate(models.Count('study_group')) )
    for key in ('control','one-way','two-way'):
        if key not in total_counts:
            total_counts[key] = 0

    email_body.append( ("Found {total} total participants. Control: {dict[control]} " +
                        "One-Way: {dict[one-way]} Two-Way: {dict[two-way]}") \
                        .format(total=sum(total_counts.values()),dict=total_counts)
                    )

    participants = participants.exclude(study_group='control')
    no_messages = []
    for p in participants:
        message = p.send_automated_message(today=date,send=send)
        if message is None:
            no_messages.append( '{} (#{})'.format( p.description(today=date),p.study_id)  )

    email_body += ['Sending to {} participants'.format(participants.count()),'']
    email_body.append( "Messages not sent: {}".format(len(no_messages)) )
    email_body.extend( "\t{}".format(d) for d in no_messages )
    email_body.append('')

def appointment_reminders(date,hour,email_body,delta_days=2,send=False):

    email_body.append( "***** Appointment Reminders *****\n" )

    # Find visits within todays
    td = datetime.timedelta(days=delta_days)
    scheduled_date = date+td
    upcoming_visits = cont.Visit.objects.filter(scheduled=scheduled_date).select_related('participant')


    extra_kwargs = {'days':delta_days,'date':scheduled_date.strftime('%b %d')}
    sent_to , control , duplicates = {} , 0 , 0
    for visit in upcoming_visits:
        if visit.participant.study_group == 'control':
            control += 1
        elif visit.participant.id in sent_to:
            duplicates += 1
        else:
            condition = '{}_pre'.format('anc' if visit.participant.is_pregnant() else 'pnc')
            message = visit.participant.send_automated_message(send=send,send_base='visit',
                            condition=condition,extra_kwargs=extra_kwargs)
            sent_to[visit.participant.id] = "{} (#{})".format(message.description(),visit.participant.study_id)



    email_body.append('Found {} visits on {}'.format(upcoming_visits.count(),date))
    email_body.append('Visit Messages Sent: {} Control: {} Duplicate: {}'.format(len(sent_to),control,duplicates) )
    email_body.extend( "\t{}".format(d) for d in sent_to.values())
