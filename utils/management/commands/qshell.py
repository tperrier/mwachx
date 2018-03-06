#!/usr/bin/python
from django.core.management.base import BaseCommand, CommandError

import contacts.models as cont
import backend.models as back
import transports.africas_talking.api as at
import datetime as dt
from django.db import models
from django.db.models import Count
import code, os

def count_field(qs,field):
    groups = qs.order_by().values(field).annotate(count=models.Count(field))
    return { g[field] : g['count'] for g in groups }

class Command(BaseCommand):
    '''Quick Shell'''

    help = "Quick Shell with default imports"

    def add_arguments(self,parser):
        parser.add_argument('--test',action='store_true',default=False,help='run test code first')

    def handle(self,*args,**options):

        # Set up a dictionary to serve as the environment for the shell, so
        # that tab completion works on objects that are imported at runtime.
        imported_objects = {}
        try:  # Try activating rlcompleter, because it's handy.
            import readline
        except ImportError:
            pass
        else:
            # We don't have to wrap the following import in a 'try', because
            # we already know 'readline' was imported successfully.
            import rlcompleter
            readline.set_completer(rlcompleter.Completer(imported_objects).complete)
            # Enable tab completion on systems using libedit (e.g. Mac OSX).
            # These lines are copied from Lib/site.py on Python 3.4.
            readline_doc = getattr(readline, '__doc__', '')
            if readline_doc is not None and 'libedit' in readline_doc:
                readline.parse_and_bind("bind ^I rl_complete")
            else:
                readline.parse_and_bind("tab:complete")

        # Get $PYTHONSTARTUP and then .pythonrc.py
        for pythonrc in (os.environ.get("PYTHONSTARTUP"), '~/.pythonrc.py'):
            if not pythonrc:
                continue
            pythonrc = os.path.expanduser(pythonrc)
            if not os.path.isfile(pythonrc):
                continue
            try:
                with open(pythonrc) as handle:
                    exec(compile(handle.read(), pythonrc, 'exec'), imported_objects)
            except NameError:
                pass

        c_all = cont.Contact.objects_no_link.all()
        m_all = cont.Message.objects.all()
        v_all = cont.Visit.objects.all()
        s_all = cont.StatusChange.objects.all()

        namespace = globals()
        namespace.update(locals())
        if options['test'] is True:
            namespace.update(test_handler(namespace))
        code.interact(local=namespace)

def test_handler(ns):

    test = "Test Working"

    yesterday = ns['c_all'].send_special_signup()

    return locals()
