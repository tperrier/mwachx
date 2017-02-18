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
            end = start + datetime.timedelta(days=1)

            messages = cont.Message.objects.filter(created__range=(start,end))
            email_body.extend( ['Message Success Stats For: {}'.format(start), ''])

            msg_groups = messages.order_by().values(
                'external_status','contact__study_group'
            ).annotate(
                count=models.Count('external_status'),
            )

            # Create OrderedDict for Groups
            status_counts = [('Success',0),('Sent',0),('',0),('Other',0),('Total',0)]
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

            email_body.append( '{:^15}{:^10}{:^10}{:^10}{:^10}{:^10}'.format('Group','Received','Missed','Sent','Other','Total') )
            total_row = collections.OrderedDict( status_counts )
            for group , status_dict in msg_dict.items():
                email_body.append( '{:^15}{:^10}{:^10}{:^10}{:^10}{:^10}'.format(
                    group,
                    status_dict['Success'],status_dict['Sent'],
                    status_dict[''],status_dict['Other'],
                    status_dict['Total']
                ) )
                for key in ['Success','Sent','','Other','Total']:
                    total_row[key] += status_dict[key]

            email_body.append( '{:^15}{:^10}{:^10}{:^10}{:^10}{:^10}'.format(
                'Total', total_row['Success'],total_row['Sent'],total_row[''],total_row['Other'],total_row['Total']
            ) )
            email_body.append('')

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
