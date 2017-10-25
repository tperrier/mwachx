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
    """ Command for checking AT Status from dump """

    help = "Check/Update AT Status From Dump"

    def add_arguments(self, parser):
        parser.add_argument('-f','--file',default='ignore/at_ids.csv',help='csv file of AT IDs')
        subparsers = parser.add_subparsers(help='AT status commands')

        stats_parser = subparsers.add_parser('stats', cmd=parser.cmd, help='print default stats')
        stats_parser.set_defaults(action='get_stats')
        stats_parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

        diff_parser = subparsers.add_parser('diff', cmd=parser.cmd, help='make a csv of the different status messages')
        diff_parser.set_defaults(action='make_diff_csv')
        diff_parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

        update_parser = subparsers.add_parser('update', cmd=parser.cmd, help='update different mxy messages')
        update_parser.set_defaults(action='update_different')
        update_parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

    def run_from_argv(self,argv):
        """
        Provide a default command (stats)
        """
        print argv
        if len(argv) == 2:
            argv.append('stats')
        super(Command,self).run_from_argv(argv)

    def handle(self,*args,**options):

        self.options = options
        getattr(self, options['action'])()

    def get_stats(self):
        """ Print basic stats about the at_ids.csv file """

        reader = csv_row_maker(self.options['file'])

        # Setup loop counter variables
        min_date , max_date = None , None
        sent_to , costs , statuses = co.Counter() , co.Counter() , co.Counter()
        found , same = co.Counter() , co.Counter()
        msg_ids = {msg.external_id:msg for msg in cont.Message.objects.filter(is_outgoing=True)}

        # Calculate stats for each row in at_id
        for row in reader:
            if max_date is None or row.date > max_date:
                max_date = row.date
            if min_date is None or row.date < min_date:
                min_date = row.date

            sent_to[row.to] += 1
            costs[row.cost] += 1
            statuses[row.status] += 1

            if row.id in msg_ids:
                found['yes'] += 1
                if row.status == msg_ids[row.id].external_status:
                    same['yes'] += 1
                else:
                    same['no'] += 1
            else:
                found['no'] += 1

        self.stdout.write( "First Message: {}\nLast Message: {}".format(min_date,max_date) )

        self.stdout.write( "Sent To Count: {} Total: {}".format(len(sent_to),sum(sent_to.values() )) )
        for number , count in sent_to.most_common(10):
            self.stdout.write( "\t{} - {}".format(number,count) )

        self.stdout.write( "\nStatuses Count: {} Total: {}".format(len(statuses),sum(statuses.values() )) )
        for status , count in statuses.most_common():
            self.stdout.write( "\t{} - {}".format(status,count) )

        self.stdout.write( "\nCosts Count: {} Total: {}".format(len(costs),sum(costs.values() )) )
        for cost , count in costs.most_common():
            self.stdout.write( "\t{} - {}".format(cost,count) )

        self.stdout.write( "\nFound" )
        for value , count in found.most_common():
            self.stdout.write( "\t{} - {}".format(value,count) )

        self.stdout.write( "\nSame" )
        for value , count in same.most_common():
            self.stdout.write( "\t{} - {}".format(value,count) )

    def make_diff_csv(self):

        reader = csv_row_maker(self.options['file'])
        msg_ids = {msg.external_id:msg for msg in cont.Message.objects.filter(is_outgoing=True)}

        writer = csv.writer( open('ignore/at_diff.csv','w') )

        writer.writerow( ('type','id','at_date','at_status','mxy_status','mxy_date') )

        for row in reader:

            if row.id in msg_ids and msg_ids[row.id].external_status != row.status:
                writer.writerow(
                    ( 'D',row.id,row.date,
                        row.status,msg_ids[row.id].external_status,
                        msg_ids[row.id].created
                    )
                )
            elif row.id not in msg_ids:
                writer.writerow( ( 'M',row.id,row.date, row.status, row.text ) )


    def update_different(self):

        reader = csv_row_maker(self.options['file'])
        msg_ids = {msg.external_id:msg for msg in cont.Message.objects.filter(is_outgoing=True)}

        count = 0
        with transaction.atomic():
            for row in reader:

                if row.id in msg_ids and msg_ids[row.id].external_status != row.status:
                    msg_ids[row.id].external_status = row.status
                    msg_ids[row.id].save()
                    count += 1
        self.stdout.write( "Updated {} messages".format(count) )

########################################
#  Utilities
########################################
def csv_row_maker(fp):
    csv_fp = csv.reader(open(fp))
    # Make header row tuple
    HeaderRow = co.namedtuple( "CSVRow",next(csv_fp) )
    row_maker = row_factory_maker( HeaderRow )
    return it.imap( row_maker , csv_fp )

def row_factory_maker(row_cls):
    """ Return a funciton that takes a row and returns a row_cls tuple
        Convert the first column from String Date to datetime
    """
    def _row_factory(row):
        new_date = datetime.datetime.strptime(row[0],"%m/%d/%y %I:%M %p")
        new_date += datetime.timedelta(hours=10) # Convert from PST to UCT
        row[0] = timezone.make_aware(new_date,timezone.utc)
        return row_cls._make(row)
    return _row_factory
