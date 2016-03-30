#!/usr/bin/python
import datetime, openpyxl as xl, os
from argparse import Namespace
import code
import operator, collections, re, argparse

from django.core.management.base import BaseCommand, CommandError

import contacts.models as cont
import command_utils
from transports.email import email
import transports.africas_talking.api as at

class Command(BaseCommand):
    '''Cron commands to manage project '''

    help = "Tools for doing specific tasks"

    def add_arguments(self,parser):
        subparsers = parser.add_subparsers(help='cron task to run')

        fix_trans = subparsers.add_parser('fix_trans',cmd=parser.cmd,help='fix translations html strings')
        fix_trans.add_argument('--dry-run',action='store_true',default=False,help='dry-run: no permenant changes')
        fix_trans.set_defaults(action='fix_trans')

    def handle(self,*args,**options):

        self.options = options
        getattr(self,options['action'])()

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
