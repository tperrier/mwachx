#!/usr/bin/python
import datetime, openpyxl as xl, os
from argparse import Namespace
import code
import operator, collections, re, argparse

#Django Imports
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection

import contacts.models as cont
import backend.models as back
import command_utils
from transports.email import email
import transports.africas_talking.api as at

class Command(BaseCommand):
    '''Cron commands to manage project '''

    help = "Tools for doing specific tasks"

    def add_arguments(self,parser):
        parser.add_argument('-t','--time',action='store_true',default=False,help='print timing information')
        subparsers = parser.add_subparsers(help='cron task to run')

        fix_trans = subparsers.add_parser('fix_trans',cmd=parser.cmd,help='fix translations html strings')
        fix_trans.add_argument('--dry-run',action='store_true',default=False,help='dry-run: no permenant changes')
        fix_trans.set_defaults(action='fix_trans')

        add_auto_trans = subparsers.add_parser('auto_trans',cmd=parser.cmd,help='add auto translations')
        add_auto_trans.add_argument('--dry-run',action='store_true',default=False,help='dry-run: no permenant changes')
        add_auto_trans.set_defaults(action='auto_trans')

    def handle(self,*args,**options):

        self.options = options
        start = datetime.datetime.now()
        getattr(self,options['action'])()
        if options['time']:
            self.stdout.write("Duration: {}".format( (datetime.datetime.now() - start)))

    def fix_trans(self):
        """ Fix translation html messages striping <br> and &nbsp; """

        regex = re.compile("&nbsp;|<br>")

        translations = cont.Message.objects.filter(translation_status="done")

        total , changed = 0 , 0
        for msg in translations:
            total += 1
            if regex.search(msg.translated_text):
                self.stdout.write( msg.translated_text )
                changed += 1
                new_text = regex.sub(' ',msg.translated_text)
                msg.translated_text = new_text
                if not self.options['dry_run']:
                    msg.save()
                self.stdout.write( new_text )
                self.stdout.write("\n")

        self.stdout.write("Total Translations: {} Changed: {}".format(total,changed) )


    def auto_trans(self):
        """ Add English translations to all auto messages

            Timing Info:
                Transaction = False | Prefetch = False
                Quries: 6712
                Total AutomatedMessages: 2259 English: 775 Changed: 1484 Not Found 0
                Duration: 0:00:49.653928

                Transaction = False | Prefetch = True
                Quries: 4454
                Total AutomatedMessages: 2259 English: 775 Changed: 1484 Not Found 0
                Duration: 0:00:47.388513

                Transaction = False | Prefetch = True
                Quries: 5229
                Total AutomatedMessages: 2259 English: 775 Changed: 1484 Not Found 0

                Transaction = True | Prefetch = True
                Quries: 2971
                Total AutomatedMessages: 2259 English: 775 Changed: 1484 Not Found 0
                Duration: 0:00:03.175598
        """

        auto_messages = cont.Message.objects.filter(translation_status='auto').prefetch_related('contact')

        with transaction.atomic():
            counts = Namespace(total=0,changed=0,not_found=[],english=0)
            for msg in auto_messages:
                counts.total += 1
                if msg.contact.language == 'english':
                    counts.english += 1
                    continue
                auto_message = back.AutomatedMessage.objects.from_description(msg.auto,exact=True)
                if auto_message:
                    msg.translated_text = auto_message.english
                    counts.changed += 1
                    if not self.options['dry_run']:
                        msg.save()
                else:
                    counts.not_found.append(msg.auto)

        self.stdout.write("Quries: {}".format(len(connection.queries)))
        self.stdout.write( ("Total AutomatedMessages: {0.total} English: {0.english} " +\
                            "Changed: {0.changed} Not Found {1}").format(counts,len(counts.not_found)))

        if counts.not_found:
            self.stdout.write("Not Found: {}".format(len(counts.not_found)))
            for description in counts.not_found:
                self.stdout.write("\t{}".format(description))
