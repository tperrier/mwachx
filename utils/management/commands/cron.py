#!/usr/bin/python
import datetime
from argparse import Namespace
import code
import operator, collections, re, argparse

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import models

import contacts.models as cont
import command_utils
from transports.email import email
import transports.africas_talking.api as at
import utils
import reports

class Command(BaseCommand):
    '''Cron commands to manage project '''

    help = "Cron commands to mange project"

    def add_arguments(self,parser):
        subparsers = parser.add_subparsers(help='cron task to run')

        nightly_parser = subparsers.add_parser('nightly',cmd=parser.cmd,help='initialize phone calls and print report')
        nightly_parser.add_argument('-c','--calls',default=False,action='store_true',help='schedule edd calls')
        nightly_parser.add_argument('-e','--email',help='send output as email',action='store_true',default=False)
        nightly_parser.add_argument('-x','--success',help='report message success stats from yesterday',action='store_true',default=False)
        nightly_parser.add_argument('-d','--delta-days',type=int,default=1,help='delta days for success count')
        nightly_parser.add_argument('-b','--balance',help='include gateway blance',action='store_true',default=False)
        nightly_parser.set_defaults(action='nightly')

        test_parser = subparsers.add_parser('test',cmd=parser.cmd,help='run test command')
        test_parser.set_defaults(action='test')

    def handle(self,*args,**options):

        self.options = options
        getattr(self,options['action'])()

    def nightly(self):
        ''' Nightly cron jobs to be run at 1am '''

        email_subject = '{}'.format( datetime.date.today().strftime('%a %b %d (%j) %Y') )
        email_body = [ "Script started at {}".format(datetime.datetime.now()),'']

        if self.options.get('balance'):
            balance = at.balance()
            email_body.extend( ['Africas Talking Balance: {}'.format(balance),''] )

        if self.options.get('success'):
            start = utils.make_date( datetime.date.today() - datetime.timedelta(days=self.options.get('delta_days') ) )
            email_body.append( reports.message_status_groups(start,delta='day') )

        if self.options.get('calls'):
            command_utils.set_edd_calls(email_body)

        email_body = '\n'.join(email_body)
        if self.options.get('email'):
            email(email_subject,email_body)
        else:
            self.stdout.write(email_subject)
            self.stdout.write(email_body)

    def test(self):
        pass
