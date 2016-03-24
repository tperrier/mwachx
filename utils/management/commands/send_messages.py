#!/usr/bin/python
import openpyxl as xl
import sys, datetime
from argparse import Namespace as ns

from django.core.management.base import BaseCommand
from django.utils import dateparse
from django.db import models


import contacts.models as cont
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
        parser.add_argument('-a','--appointment',help='send visit reminders',action='store_true',default=False)
        parser.add_argument('-m','--missed',help='send visit missed visit reminders',action='store_true',default=False)

    def handle(self,*args,**options):
        if options.get('test'):
            self.stdout.write( 'Time: {}\nVersion: {}\nPath: {}\n'.format(datetime.datetime.now(),sys.version,sys.path) )
            self.stdout.write( str(options) )
            return None

        # Check for required arguments
        required = ['weekly','appointment','missed']
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

        # Convert hour to 8,13 or 20
        hour = [0,8,8,8,8,  8,8,8,8,8, 8,13,13,13,13, 13,20,20,20,20, 20,20,20,20][hour]

        send = options.get('send')
        email_subject = '{}{}'.format( date.strftime('%a %b %d (%j) %Y'), '' if options.get('send') else ' (FAKE)' )
        email_body = [ "Script started at {}".format(datetime.datetime.now()),
                        "Options: {} D:{} H:{} Send:{}".format(date,day,hour,send), '' ]

        if options["weekly"]:
            weekly_messages(day,hour,date,email_body,send=send)
        if options["appointment"]:
            appointment_reminders(date,hour,email_body,send=send)
        if options["missed"]:
            missed_visit_reminders(hour,email_body,send=send)

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

    vals = ns(times={8:0,13:0,20:0}, control=0, no_messages=[],sent_to=[])
    for p in participants:
        if p.study_group == 'control':
            vals.control += 1
        else:
            vals.times[p.send_time] += 1
            if hour==0 or hour==p.send_time:
                message = p.send_automated_message(today=date,send=send)
                if message is None:
                    vals.no_messages.append( '{} (#{})'.format( p.description(today=date),p.study_id)  )
                else:
                    vals.sent_to.append( "{} (#{}) {}".format(message.description(),p.study_id,p.send_time) )

    email_body.append( "Found {} participants for {}".format(participants.count(),date.strftime("%A")) )
    email_body.append( "Control: {0.control} 8h: {0.times[8]} 13h: {0.times[13]} 20h: {0.times[20]}".format(vals) )

    email_body.append( "Sending to {} participants".format( len(vals.sent_to)) )
    email_body.extend( "\t{}".format(d) for d in vals.sent_to )
    email_body.append('')

    email_body.append( "Messages not sent: {}".format(len(vals.no_messages)) )
    email_body.extend( "\t{}".format(d) for d in vals.no_messages )
    email_body.append('')

def appointment_reminders(date,hour,email_body,send=False):

    email_body.append( "***** Appointment Reminders *****\n" )
    # Find visits scheduled within delta_days and not attended early
    scheduled_date = date + datetime.timedelta(days=2)
    upcoming_visits = cont.Visit.objects.pending(scheduled=scheduled_date)\
        .exclude(visit_type='study').select_related('participant')

    vals = ns(sent_to={}, no_messages=[], control=0, duplicates=0 , times={8:0,13:0,20:0})
    for visit in upcoming_visits:
        if visit.participant.study_group == 'control':
            vals.control += 1
        elif visit.participant.id in vals.sent_to:
            vals.duplicates += 1
        else:
            vals.times[visit.participant.send_time] += 1
            if hour == 0 or visit.participant.send_time == hour:
                message = visit.send_visit_reminder(send=send)

                if message is None:
                    condition = visit.get_condition('pre')
                    vals.no_messages.append('{}-{}'.format(visit.participant.description(),condition))
                else:
                    vals.sent_to[visit.participant.id] = "{} (#{})".format(
                        message.description(),visit.participant.study_id
                    )

    email_body.append('Found {} visits on {}'.format(upcoming_visits.count(),scheduled_date))
    email_body.append(
        ('Control: {0.control} Duplicate: {0.duplicates} 8h: {0.times[8]} 13h: {0.times[13]} 20h: {0.times[20]}' \
        + '\n\tSent: {1}').format(vals,len(vals.sent_to))
    )
    email_body.extend( "\t{}".format(d) for d in vals.sent_to.values())
    email_body.append('')

    email_body.append( "Messages not sent: {}".format(len(vals.no_messages)) )
    email_body.extend( "\t{}".format(d) for d in vals.no_messages )
    email_body.append('')

def missed_visit_reminders(hour,email_body,send=False):

    email_body.append( "***** Missed Visit Reminders *****\n" )
    missed_visits = cont.Visit.objects.get_missed_visits()

    vals = ns(sent_to=[], no_messages=[], control=0, times={8:0,13:0,20:0})
    for visit in missed_visits:
        if visit.participant.study_group == 'control':
            vals.control += 1
        else:
            vals.times[visit.participant.send_time] += 1
            if hour == 0 or visit.participant.send_time == hour:
                message = visit.send_missed_visit_reminder(send=send)

                if message is None:
                    condition = visit.get_condition('missed')
                    vals.no_messages.append('{}-{}'.format(visit.participant.description(),condition))
                else:
                    vals.sent_to.append( "{} (#{})".format(message.description(),visit.participant.study_id) )

    email_body.append(
        'Total: {0} Control: {1.control} 8h: {1.times[8]} 13h: {1.times[13]} 20h: {1.times[20]}\n\tSent: {2}'.format(
            len(missed_visits),vals,len(vals.sent_to)
        )
    )
    email_body.extend( "\t{}".format(d) for d in vals.sent_to)
    email_body.append('')

    email_body.append( "Messages not sent: {}".format(len(vals.no_messages)) )
    email_body.extend( "\t{}".format(d) for d in vals.no_messages )
    email_body.append('')
