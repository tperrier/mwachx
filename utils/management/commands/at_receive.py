# Python Imports
import datetime
import csv
import argparse
import os
import pytz

# Django Imports
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import models , transaction

# Local Imports
import contacts.models as cont
import transports

PCT = pytz.timezone('US/Pacific')

class Command(BaseCommand):
    """
    Import incomming messages from the Africa's Talking export.

    Columns:
        - Date
        - MessageId (This seems to be the count of interna to AT)
        - From
        - To
        - Text
    """

    help = "manage success/sent time from AT message dump"

    def add_arguments(self,parser):

        parser.add_argument('-f','--file',default='ignore/at_incomming.csv',help='file with incomming messages')
        parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter

    def handle(self,*args,**options):

        with open(options['file']) as fp:
            csv_reader = csv.reader(fp)
            csv_reader.next() # skip header
            for row in csv_reader:
                kwargs = parse_incomming(row)
                message = transports.receive(kwargs['identity'],kwargs['text'],kwargs['external_id'],bulk=True)
                message.created = kwargs['created']
                message.save()
                print message.contact, message.created , message.text, kwargs['created'] , row[0]

########################################
# Helper Functions And Utilities
########################################

def parse_incomming(row):
    """
    Convert a csv row of incomming messages from AT into a dictionary
    """
    created = timezone.make_aware(datetime.datetime.strptime(row[0],'%m/%d/%y %I:%M %p') + datetime.timedelta(hours=10))
    return {
        'created' : created,
        'external_id' : row[1],
        'identity' : '+'+row[2],
        'text' : row[4],
    }
