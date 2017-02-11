#!/usr/bin/python
import datetime, openpyxl as xl, os
from argparse import Namespace
import code
import operator, collections, re, csv
import importlib

#Django Imports
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connection

import contacts.models as cont
import backend.models as back
import command_utils
import transports
from transports.email import email
import transports.africas_talking.api as at
import tasks 

class Command(BaseCommand):
    '''Cron commands to manage project '''

    help = "Tools for doing specific tasks"

    def add_arguments(self,parser):
        parser.add_argument('-t','--time',action='store_true',default=False,help='print timing information')
        subparsers = parser.add_subparsers(help='task to run')

        fix_trans = subparsers.add_parser('fix_trans',cmd=parser.cmd,help='fix translations html strings')
        fix_trans.add_argument('--dry-run',action='store_true',default=False,help='dry-run: no permenant changes')
        fix_trans.set_defaults(action='fix_trans')

        add_auto_trans = subparsers.add_parser('auto_trans',cmd=parser.cmd,help='add auto translations')
        add_auto_trans.add_argument('--dry-run',action='store_true',default=False,help='dry-run: no permenant changes (defatul: True)')
        add_auto_trans.set_defaults(action='auto_trans')

        send_from_csv = subparsers.add_parser('send_csv',cmd=parser.cmd,help='send messages from Africas Talking csv dump')
        send_from_csv.add_argument('csv_file',help='csv file to use for sending messages from')
        send_from_csv.add_argument('-s','--send',action='store_true',default=False,help='send messages otherwise dry-run')
        send_from_csv.set_defaults(action='send_csv')

        task_parser = subparsers.add_parser('tasks',cmd=parser.cmd,help='run one off task from task folder')
        task_parser.add_argument('--run',action='store_true',default=False,help='run: flag to make changes (defatul: False)')
        task_parser.add_argument('task',choices=tasks.task_list,help='task to run')
        task_parser.add_argument('task_args',nargs="?",default="main",help="extra arguments as string for task")
        task_parser.set_defaults(action='run_task')

    def handle(self,*args,**options):

        self.options = options
        start = datetime.datetime.now()
        getattr(self,options['action'])()
        if options['time']:
            self.stdout.write("Duration: {}".format( (datetime.datetime.now() - start)))

    def run_task(self):

        module = importlib.import_module('utils.management.commands.tasks.fix_{}'.format(self.options['task']))
        tasks.utils.dispatch(module,self.options['task_args'],not self.options['run'])

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

    def send_csv(self):
        """ Send messages from a csv file.

            csv columns: Date	To	Status	Action	Message
            If Action is has text do not send that message
        """

        csv_file = csv.reader(open(self.options['csv_file']))

        # Print CSV Header
        print "Header:" , csv_file.next() , "Send:" , self.options['send']
        print ""

        sent , missing , skipped = 0 , 0 , 0
        for row in csv_file:
            _ , phone_number , _ , action , text = row
            phone_number = "+" + phone_number

            if action.strip() == "":
                try:
                    contact = cont.Contact.objects.get_from_phone_number(phone_number)
                except cont.Contact.DoesNotExist as e:
                    print "Missing:" , phone_number , " -> " , text
                    if self.options['send']:
                        transports.send( phone_number , text )
                    missing += 1
                else:
                    if self.options['send']:
                        contact.send_message( text )
                    sent += 1
            else:
                skipped += 1

        print "Sent:" , sent , "Missing:" , missing , "Skipped:" , skipped
