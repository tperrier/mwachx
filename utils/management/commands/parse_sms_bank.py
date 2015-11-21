#!/usr/bin/python
from optparse import make_option
import datetime, openpyxl as xl
import code
import operator, collections, re

from django.core.management.base import BaseCommand, CommandError
import utils.sms_utils as sms

class Command(BaseCommand):

    help = 'Parse and import SMS data bank'
    args = '<FILE>'
    option_list = BaseCommand.option_list + (
        # make_option('-f','--file',help='file name to import',metavar='FILE',default=None),
    )

    def handle(self,*args,**options):
        file_name = try_args(args,0,'No file name provided')
        try:
            command = args[1]
        except IndexError:
            print 'No Command Found',action_list
            return
        if command not in action_list:
            print "Command: {} not valid.".format(command),action_list

        wb = xl.load_workbook(file_name)

        if command == 'print':
            anc_ws = wb.worksheets[0]
            print_statistics(anc_ws)
        elif command == 'xlsx':
            anc_ws = wb.worksheets[0]
            new_wb = xl.workbook.Workbook()
            make_ws(anc_ws,new_wb)
            new_wb.save('ignore/new.xlsx')
        elif command == 'make_translations':
            translations = xl.workbook.Workbook()
            try:
                old_translation_file = try_args(args,2,'No Old Translation File Found')
                old_translation_wb = xl.load_workbook(old_translation_file)
                translation_ws = old_translation_wb.active
            except CommandError as e:
                translation_ws = None
            make_translations(wb,translations.active,translation_ws)
            translations.save('ignore/mx_sms_translations_new.xlsx')


########################################
# Actions
########################################
Action = collections.namedtuple('Action',('action','help'))
actions = [
    Action('print','print group message counts'),
    Action('xlsx','make new xlsx'),
    Action('make_translations','make translations'),
    Action('import','import messages into backend.AutomatedMessage'),
]
action_list = [a.action for a in actions]

########################################
#  Utility Functions
########################################
def recursive_dd():
    return collections.defaultdict(recursive_dd)

def print_statistics(ws):
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

def make_ws(ws,wb):
    new_ws = wb.active
    # Header Row
    new_ws.append(sms.cell_values(*ws.rows[0]))
    for row in ws.rows[1:]:
        msg = sms.MessageRow(row)
        if msg.is_valid():
            new_ws.append(msg.make_row(row))

def make_translations(in_wb,new_ws,old_translations=None):
    new_ws.append(sms.MessageRow.translation_header())
    old_translations = {} if old_translations == None else sms.message_dict(old_translations,translation=True)
    todo_count = 0
    for row in in_wb.get_sheet_by_name('anc').rows[1:]:
        msg = sms.MessageRow(row)
        if msg.is_valid():
            row = msg.make_translation(old_translations)
            if row[0] == '!':
                todo_count += 1
            new_ws.append(row)
    for row in in_wb.get_sheet_by_name('special').rows[1:]:
        msg = sms.MessageRow(row)
        if msg.is_valid():
            row = msg.make_translation(old_translations)
            if row[0] == '!':
                todo_count += 1
            new_ws.append(row)
    print 'Todo:',todo_count
    new_ws.freeze_panes = 'A2'

def try_args(args,index,msg):
    try:
        return args[index]
    except IndexError as e:
        raise CommandError(msg)
