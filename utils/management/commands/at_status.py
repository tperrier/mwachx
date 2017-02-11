# Python Imports
import datetime
import csv
import itertools as it
import collections as co
import argparse
import os

# Django Imports
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import models , transaction

# Local Imports
import contacts.models as cont

class Command(BaseCommand):

    help = "manage success/sent time from AT message dump"

    def add_arguments(self,parser):

        parser.add_argument('-d','--dir',default='ignore/at_ids',help='default base dir')
        parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

        subparsers = parser.add_subparsers(help='at status actions')

        # The cmd argument is required for django.core.management.base.CommandParser
        find_parser = subparsers.add_parser('find',cmd=parser.cmd,help='find AT IDs')
        find_parser.set_defaults(action='find_at_ids')
        find_parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

        zeros_parser = subparsers.add_parser('zeros',cmd=parser.cmd,help="find AT IDs for zeros")
        zeros_parser.set_defaults(action='find_zero_ids')
        zeros_parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

        check_parser = subparsers.add_parser('check',cmd=parser.cmd,help='check csv files')
        check_parser.add_argument('input_csv',nargs='?',default='at_merged_list.csv',help='input csv file to check')
        check_parser.set_defaults(action='check_csv')
        check_parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

        current_parser = subparsers.add_parser('current',cmd=parser.cmd,help='current csv files')
        current_parser.set_defaults(action='current_status')
        current_parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

        make_parser = subparsers.add_parser('make',cmd=parser.cmd,help='make final update list')
        make_parser.add_argument('input_csv',nargs='?',default='at_merged_list.csv',help='input csv file to check')
        make_parser.set_defaults(action='make_update_list')
        make_parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

        update_parser = subparsers.add_parser('update',cmd=parser.cmd,help='update database')
        update_parser.add_argument('input_csv',nargs='?',default='at_update_ids.csv',help='input csv file to check')
        update_parser.add_argument('--live-run',action='store_true',default=False,help='make updates')
        update_parser.set_defaults(action='update_ids')
        update_parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

    def handle(self,*args,**options):

        print options
        self.options = options
        getattr(self,options['action'])()

    def find_at_ids(self):

        self.print_header( "Finding AT Ids" )

        self.stdout.write( self.style.ERROR( 'Exiting' ) )
        return

        at_msg_ids = csv.writer(open("ignore/at_msg_ids.csv",'w'))
        at_msg_ids.writerow( ('date','to','identity','at_id','at_status','msg_status','msg') )

        at_msg_ids_2 = csv.writer(open('ignore/at_msg_ids_2.csv','w'))
        at_msg_ids_2.writerow( ('date','to','identity','at_id','status','msg_status','msg') )

        at_msg_ids_0 = csv.writer(open('ignore/at_msg_ids_0.csv','w'))
        at_msg_ids_0.writerow( ('date','to','status','msg') )

        at_csv = csv.reader(open("ignore/2017_01_31_at_dump.csv"))

        # Make header row tuple
        HeaderRow = co.namedtuple( "HeaderRow",next(at_csv) )
        row_maker = row_factory_maker( HeaderRow )

        for row in it.imap(row_maker, at_csv ):
            msgs = find_msg_match(row)

            if msgs.count() == 1:
                msg = msgs.first()
                at_msg_ids.writerow( (
                    row.date,
                    row.to,
                    msg.connection.identity,
                    msg.external_id,
                    row.status,
                    msg.external_status,
                    row.msg
                ) )
            elif msgs.count() > 1:
                for msg in msgs:
                    at_msg_ids_2.writerow( (
                        row.date,
                        row.to,
                        msg.connection.identity,
                        msg.external_id,
                        row.status,
                        msg.external_status,
                        row.msg
                    ) )
            else:
                at_msg_ids_0.writerow( (row.date, row.to, row.status, row.msg) )

    def check_csv(self):

        at_csv = csv_row_maker( self.dir_fp(self.options['input_csv']) )

        counts = co.Counter( (row.at_status,row.msg_status) for row in at_csv )
        for count in counts.items():
            print count
        self.stdout.write( self.style.SQL_KEYWORD( 'Total: {}'.format( sum(counts.values()) ) ) )

    def current_status(self):

        self.print_header( 'Current Status' )

        counts = cont.Message.objects.order_by().values('external_status').annotate(count=models.Count('external_status'))

        for count in counts:
            self.stdout.write( "  Status: {0[external_status]:<20.16} Count: {0[count]}".format(count) )

    def make_update_list(self):

        at_csv = csv_row_maker( self.dif_fp(self.options['input_csv']) )

        at_final = csv.writer(open(self.dif_fp('at_update_ids.csv'),'w'))
        at_final.writerow( ('date','at_id','at_status','msg_status') )

        for row in it.imap( row_maker , at_csv):
            if row.status != row.msg_status:
                at_final.writerow( (
                    row.date,
                    row.at_id,
                    row.status,
                    row.msg_status
                ))

    def update_ids(self):

        self.print_header( "Update: Live={}".format(self.options['live_run']) )

        at_csv = csv_row_maker( self.dir_fp(self.options['input_csv']) )

        scheduled , updated = 0 , 0
        with transaction.atomic():
            for row in at_csv:
                if row.at_status != row.msg_status:
                    scheduled += 1
                    if self.options['live_run']:
                        updated += cont.Message.objects.filter(external_id=row.at_id).update(external_status=row.at_status)

        self.stdout.write( self.style.WARNING( "Scheduled: {} Updated: {}".format(scheduled,updated) ) )

    def print_header(self,header):
        self.stdout.write( self.style.WARNING( '*' * 50 + '\n*' ), ending='' )
        self.stdout.write( self.style.SQL_KEYWORD( '{:^48}'.format(header) ), ending='' )
        self.stdout.write( self.style.WARNING( '*\n' + '*' * 50 ) )

    def dir_fp(self,fp):
        return os.path.join(self.options['dir'],fp)

########################################
#  Utilities
########################################
def csv_row_maker(fp):
    csv_fp = csv.reader(open(fp))
    # Make header row tuple
    HeaderRow = co.namedtuple( "HeaderRow",next(csv_fp) )
    row_maker = row_factory_maker( HeaderRow )
    return it.imap( row_maker , csv_fp )

def row_factory_maker(row_cls):
    """ Return a funciton that takes a row and returns a row_cls tuple
        Convert the first column from String Date to datetime
    """
    def _row_factory(row):
        try:
            new_date = datetime.datetime.strptime(row[0],"%I:%M %p %B %d, %Y")
            new_date -= datetime.timedelta(hours=3) # Convert from EAT to UCT
        except ValueError as e:
            new_date = datetime.datetime.strptime(row[0],"%Y-%m-%d %H:%M:%S+00:00")
        row[0] = timezone.make_aware(new_date,timezone.utc)
        return row_cls._make(row)
    return _row_factory

def find_msg_match(row,with_text=True,td=1):
    end_time = row.date + datetime.timedelta(minutes=td)
    identity = "+%s" % row.to
    msg_Q = models.Q(created__range=(row.date,end_time),connection__identity=identity)
    if with_text is True:
        msg_Q &= models.Q(text=row.msg.strip())
    msgs = cont.Message.objects.filter(msg_Q)
    return msgs
