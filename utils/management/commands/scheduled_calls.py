#!/usr/bin/python
import datetime, openpyxl as xl, os
from argparse import Namespace
import code
import operator, collections, re, argparse

from django.core.management.base import BaseCommand, CommandError
import contacts.models as cont

class Command(BaseCommand):
    ''' Manage 1mo and 1yr calls
        actions:
            - nightly: run nightly tasks
            - init: schedule calls for clients that need them.
    '''

    help = "Manage 1mo and 1yr calls"

    def add_arguments(self,parser):
        subparsers = parser.add_subparsers(help='manage scheduled calls')

        init_parser = subparsers.add_parser('init',cmd=parser.cmd,help='initialize phone calls and print report')
        init_parser.set_defaults(action='initialize')

        test_parser = subparsers.add_parser('test',cmd=parser.cmd,help='run test command')
        test_parser.set_defaults(action='test')

    def handle(self,*args,**options):

        self.options = options
        getattr(self,options['action'])()

    def initialize(self):
        self.stdout.write( "{0} Initializing Phonecalls {0}\n".format('*'*5) )

        post = cont.Contact.objects.filter(status='post').order_by('delivery_date')
        for c in post:
            month_created , month_call = None , None
            if c.delta_days() < 30:
                month_created , month_call = c.schedule_month_call(created=True)
            year_created , year_call = c.schedule_year_call(created=True)
            if month_created or year_created:
                self.stdout.write( "{!r:35} {} ({}) M[{} {}] Y[{} {}]".format(
                    c,c.delivery_date,c.delta_days(),
                    month_created, month_call,
                    year_created, year_call
                ) )

    def test(self):
        self.stdout.write( "{0} Running Test Command {0}".format('*'*5) )

def set_edd_calls(email_body):
    ''' Set 14 day post edd call if still pregnant on edd
    To be run every night at 12am'''

    email_body.append( "***** Set EDD Calls *****\n" )

    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    edd_today = cont.Contact.objects.filter(due_date=yesterday,status='edd',delivery_date__isnull=True)

    email_body.append( "Found {} post edd participants on {}".format(len(edd_today),yesterday) )

    for post in edd_today:
        post.schedule_edd_call()
        email_body.append( "\t{!r}".format(post) )
