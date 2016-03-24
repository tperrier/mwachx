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
        """ Find all postpartum participants and schedule 1mo and 1yr call """
        self.stdout.write( "{0} Initializing Phonecalls {0}\n".format('*'*5) )

        post = cont.Contact.objects.filter(status='post').order_by('delivery_date')
        total_post , total_created = 0 , 0
        for c in post:
            total_post += 1
            month_created , month_call = None , None
            if c.delta_days() < 30:
                month_created , month_call = c.schedule_month_call(created=True)
            year_created , year_call = c.schedule_year_call(created=True)
            if month_created or year_created:
                total_created += 1
                self.stdout.write( "{!r:35} {} ({}) M[{} {}] Y[{} {}]".format(
                    c,c.delivery_date,c.delta_days(),
                    month_created, month_call,
                    year_created, year_call
                ) )
        self.stdout.write( "Total Post: {} Created: {} Not-Created: {}\n".format(total_post,total_created,total_post-total_created) )

        # Schedule calls for postdate participants
        today = datetime.date.today()
        over = cont.Contact.objects.filter(status='pregnant',due_date__lte=today).order_by('due_date')
        total_over , total_created = 0 , 0
        for c in over:
            total_over += 1
            month_created , month_call = c.schedule_edd_call(created=True)
            if month_created:
                total_created += 1
                self.stdout.write ( "{!r:35} {} ({})".format(c,c.due_date,c.delta_days()) )

        self.stdout.write( "Total Over: {} Created: {} Not-Created: {}\n".format(total_over,total_created,total_over-total_created) )

    def test(self):
        self.stdout.write( "{0} Running Test Command {0}".format('*'*5) )
