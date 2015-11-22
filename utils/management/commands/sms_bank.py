#!/usr/bin/python
from optparse import make_option
import datetime, openpyxl as xl
import code
import operator, collections, re, argparse

from django.core.management.base import BaseCommand, CommandError
import utils.sms_utils as sms
import backend.models as back

class Command(BaseCommand):

    help = 'Parse and import SMS data bank'

    def add_arguments(self,parser):
        # code.interact(local=locals())
        subparsers = parser.add_subparsers(help='sms bank commands')

        # The cmd argument is required for django.core.management.base.CommandParser
        make_parser = subparsers.add_parser('make',cmd=parser.cmd,help='make translations help')
        make_parser.add_argument('bank',help='new Excel file SMS bank')
        make_parser.add_argument('old',nargs='?',help='old message translations',default=None)
        make_parser.set_defaults(action='make_translations')

        print_parser = subparsers.add_parser('print',cmd=parser.cmd,help='show statistics from  SMS Excel bank')
        print_parser.add_argument('bank',help='Excel file SMS bank')
        print_parser.set_defaults(action='print_statistics')

        import_parser = subparsers.add_parser('import',cmd=parser.cmd,help='import messages from SMS Excel bank')
        import_parser.add_argument('bank',help='translated SMS bank')
        import_parser.add_argument('--done',default=False,action='store_true',help='Only import messages marked as done')
        import_parser.set_defaults(action='import_messages')

    def handle(self,*args,**options):

        getattr(self,options['action'])(options)

        if False:
            anc_ws = wb.worksheets[0]
            new_wb = xl.workbook.Workbook()
            make_ws(anc_ws,new_wb)
            new_wb.save('ignore/new.xlsx')

    ########################################
    # Commands
    ########################################
    def print_statistics(self,options):
        sms_bank = xl.load_workbook(options['bank'])
        ws = sms_bank.worksheets[0]

        messages = sms.parse_messages(ws)
        stats = recursive_dd()
        for msg in messages:
            base = stats[msg.send_base]
            group = base[msg.group]
            track = group[msg.track]
            track.default_factory = int
            track['yes' if msg.hiv else 'no'] += 1

        for base, groups in stats.items():
            for group, tracks in groups.items():
                for track, hiv_messaging in tracks.items():
                    for hiv, count in hiv_messaging.items():
                        print "{}_{}_{}_{}: {}".format(base,group,track,hiv,count)

    def make_translations(self,options):
        sms_bank = xl.load_workbook(options['bank'])

        translations = xl.workbook.Workbook()
        new_ws = translations.active
        new_ws.append(sms.MessageRow.translation_header())

        if options['old'] is None:
            old_translations = {}
        else:
            old_translation_wb = xl.load_workbook(options['old'])
            old_translations = sms.message_dict(old_translation_wb.worksheets[0],translation=True)

        todo_count = 0
        for row in sms_bank.get_sheet_by_name('anc').rows[1:]:
            msg = sms.MessageRow(row)
            todo_count += msg.add_translation(new_ws,old_translations)
        for row in sms_bank.get_sheet_by_name('special').rows[1:]:
            msg = sms.MessageRow(row)
            todo_count += msg.add_translation(new_ws,old_translations)

        print 'Todo:',todo_count
        new_ws.freeze_panes = 'A2'
        new_ws.auto_filter.ref = 'A1:K1'

        column_widths = {'A':4,'D':6,'E':6,'F':6,'G':45,'H':45,'I':45,'J':45}
        for col_letter, width in column_widths.items():
            new_ws.column_dimensions[col_letter].width = width

        translations.save('ignore/mx_sms_translations_new.xlsx')

    def import_messages(self,options):
        sms_bank = xl.load_workbook(options['bank'])
        do_all = not options['done']

        todo,total = 0,0
        for row in sms_bank.active.rows[1:]:
            msg = sms.MessageRow(row,translation=True)
            total += 1
            if do_all or msg.status == 'done':
                auto = back.AutomatedMessage.objects.from_excel(msg)
                if msg.status == 'todo':
                    self.stdout.write('Warning: message {} still todo'.format(msg.description()))
                    todo += 1
        self.stdout.write('Messages Imported: {} Messages Todo: {}'.format(total,todo))


########################################
#  Utility Functions
########################################
def recursive_dd():
    return collections.defaultdict(recursive_dd)

def make_ws(ws,wb):
    new_ws = wb.active
    # Header Row
    new_ws.append(sms.cell_values(*ws.rows[0]))
    for row in ws.rows[1:]:
        msg = sms.MessageRow(row)
        if msg.is_valid():
            new_ws.append(msg.make_row(row))
