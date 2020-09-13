#!/usr/bin/python
from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string

import contacts.models as cont
import backend.models as back

from django.db import models
from django.db.models import Count

import collections as col
import code, os
import datetime as dt

class Command(BaseCommand):
    '''Create a static site for archive'''

    help = "Create a static site for archive"

    def add_arguments(self, parser):
        parser.add_argument('-d','--dir', default='static_archive', help='folder to save files in')
        parser.add_argument('-i', '--index', default=False, action='store_true', help='only make index')

    def handle(self, *args, **options):

        self.make_index(options['dir'])
        if options['index']:
            return

        for participant in cont.Contact.objects.annotate_messages().all():
            self.make_participant_file(participant, options['dir'])

    def make_index(self, base_dir):
        context = {
         'participants': cont.Contact.objects.all(),
         'static_dir': 'participants/',
        }
        with open('{}/index.html'.format(base_dir),'w') as fp:
            raw_html = render_to_string("static_archive/index.html", context)
            fp.write(raw_html.encode('utf8'))

    def make_participant_file(self, participant, base_dir):

        context = {'p':participant}
        with open('{}/participants/{}.html'.format(base_dir,participant.study_id),'w') as fp:
            raw_html = render_to_string("static_archive/participant.html",context)
            fp.write(raw_html.encode('utf8'))
