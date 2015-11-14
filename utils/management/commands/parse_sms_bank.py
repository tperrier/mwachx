#!/usr/bin/python
from optparse import make_option
import datetime, openpyxl as xl
import code
import operator, collections, re

from django.core.management.base import BaseCommand, CommandError

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


########################################
# Actions
########################################
Action = collections.namedtuple('Action',('action','help'))
actions = [
    Action('print','print group message counts'),
    Action('xlsx','make new xlsx'),
]
action_list = [a.action for a in actions]

########################################
#  Utility Functions
########################################
class MessageRow(object):

    def __init__(self,row):
        dx = 1 if row[0].value == '#' else 0
        self.group, self.track, self.hiv, self.send_base = cell_values(*operator.itemgetter(0+dx,1+dx,2+dx,3+dx)(row))
        self.english, self.swahili, self.luo, self.comment = cell_values(*operator.itemgetter(5+dx,8+dx,9+dx,10+dx)(row))
        if self.hiv is not None:
            self.hiv = False if self.hiv.strip().lower() == 'no' else True
        self.offset = self.get_offset()
        self.row = row[0].row
        self.dx = dx

    def get_offset(self):
        if self.send_base == 'signup':
            return 1
        elif self.send_base == 'edd':
            comment = self.parse_comment()
            if comment is None:
                return None
            return 40 - comment
        elif self.send_base == 'dd':
            if self.comment.startswith('(Once'):
                return 0
            return self.parse_comment()

    def parse_comment(self):
        try:
            match = re.search('\d+',self.comment)
        except TypeError as e:
            return None
        if match is None:
            print 'Comment Warning:',self.comment
            return None
        return int(match.group(0))

    def __str__(self):
        return "{0.send_base}_{0.group}_{0.track}_{0.hiv}".format(self)

    def is_valid(self):
        group_valid = self.group in ['one_way','two_way']
        has_offset = self.offset is not None

        return group_valid and has_offset

    def make_row(self,row):
        row = cell_values(*row)
        if self.is_valid():
            row[4+self.dx] = self.offset
        if self.dx == 0:
            return [None if self.is_valid() else '#']  + row
        return row

def recursive_dd():
    return collections.defaultdict(recursive_dd)

def print_statistics(ws):
    messages = parse_messages(ws)
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

def parse_messages(ws):
    messages = []
    for row in ws.rows[1:]:
        msg = MessageRow(row)
        if msg.is_valid():
            messages.append(MessageRow(row))
        else:
            print 'Row {} invalid: {}'.format(msg.row,msg)
    return messages

def make_ws(ws,wb):
    new_ws = wb.active
    for row in ws.rows:
        msg = MessageRow(row)
        new_ws.append(msg.make_row(row))

def cell_values(*args):
    if len(args) == 1:
        return args[0].value
    return [arg.value for arg in args]

def try_args(args,index,msg):
    try:
        return args[index]
    except IndexError as e:
        raise CommandError(msg)
