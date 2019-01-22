#!/usr/bin/python
import openpyxl as xl
import sys, datetime
from argparse import Namespace as ns
from requests import HTTPError

from django.core.management.base import BaseCommand
from django.utils import dateparse
from django.db import models


import contacts.models as cont
import transports
from transports.email import email


class Command(BaseCommand):

    help = 'send test messages to a phone in Kenya'

    def add_arguments(self, parser):
        parser.add_argument('-s', '--send', help='flag for sending (False)', action='store_true', default=False)
        parser.add_argument('-e', '--email', help='send output as email', action='store_true', default=False)
        parser.add_argument('--date', default='', help='set testing date y-m-d')
        parser.add_argument('--time', default='', help='set testing time h:m')
        parser.add_argument('--start', default='2019-01-22 10:00', help='time to start sending (YYYY-MM-DD HH:MM)')

    def handle(self,*args,**options):

        # Try to parse the date option or use current date
        date = options.get('date')
        try:
            date = datetime.datetime.strptime(date,'%Y-%m-%d').date()
        except ValueError as e:
            # Invlaid date string so set to today
            date = datetime.date.today()

        time = options.get('time')
        try:
            time = datetime.datetime.strptime(time,'%H:%M').time()
        except ValueError as e:
            # Invalid time string so set time to now
            time = datetime.datetime.now().time()

        start = datetime.datetime.strptime(options.get('start'),'%Y-%m-%d %H:%M')
        now = datetime.datetime.combine(date,time)
        delta = (now - start).total_seconds() / 3600
        # round to closest 0.25
        delta = (delta*1000) // 1 + 125
        _ , r = divmod(delta, 250)
        delta = (delta - r) / 1000

        day_intervals = [.25, 6, 12, 18, 23.5, 23.75, 24]
        intervals = [-.25, 0] +[ i+(d*24) for d in (0,1,2,3) for i in day_intervals]
        valid_time = delta in intervals

        if not valid_time:
            print 'Invalid Time -- Delta:' , delta
            print intervals
            return


        send = options.get('send')
        email_subject = '{}{}'.format( date.strftime('%a %b %d (%j) %Y'), '' if options.get('send') else ' (FAKE)' )
        email_body = [ "Script started at {}".format(datetime.datetime.now()),
                        "Start: {}\nTime:  {}\nDelta: {} Valid: {} Send: {}".format(start,now,delta,send,valid_time),
                        '' ]
        if send is True:
            test_participant = cont.Contact.objects.get(study_id='12345000001')
            message = 'AT_Message: {0} {1}'.format(intervals.index(delta) + 1, now)
            test_participant.send_message(message, is_system=False, auto='msg_delivery_test', topic='testing')

        email_body = '\n'.join(email_body)
        if options.get('email'):
            email(email_subject,email_body)
        else:
            self.stdout.write(email_subject)
            self.stdout.write(email_body)
