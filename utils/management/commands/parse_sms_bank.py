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
        wb = xl.load_workbook(file_name)
        anc_ws = wb.worksheets[0]

        for row in anc_ws.rows[1:5]:
            row = MessageRow(row)
            print str(row)


########################################
#  Utility Functions
########################################
class MessageRow(object):

    def __init__(self,row):
        self.group, self.track, self.hiv, self.send_base = cell_values(*operator.itemgetter(0,1,2,3)(row))
        self.english, self.swahili, self.luo, self.comment = cell_values(*operator.itemgetter(5,8,9,10)(row))
        self.hiv = False if self.hiv.strip().lower() == 'no' else True
        self.offset = self.get_offset()

    def get_offset(self):
        if self.send_base == 'signup':
            return 1
        elif self.send_base == 'edd':
            return 40 - self.parse_comment()
        elif self.send_base == 'dd':
            return self.parse_comment()

    def parse_comment(self):
        match = re.search('\d+',self.comment)
        if match is None:
            print 'Comment Warning:',self.comment
        return int(match.group(0))

    def __str__(self):
        return str(self.__dict__)

def cell_values(*args):
    if len(args) == 1:
        return args[0].value
    return (arg.value for arg in args)

def try_args(args,index,msg):
    try:
        return args[index]
    except IndexError as e:
        raise CommandError(msg)
