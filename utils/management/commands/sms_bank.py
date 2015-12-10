#!/usr/bin/python
import datetime, openpyxl as xl, os
from argparse import Namespace
import code
import operator, collections, re, argparse

from django.core.management.base import BaseCommand, CommandError
import utils.sms_utils as sms
import backend.models as back

class Command(BaseCommand):

    help = 'Parse and import SMS data bank'

    class Paths:
        base = 'translations'
        bank = os.path.join(base,'bank.xlsx')

        todo_swahili = os.path.join(base,'todo_swahili.xlsx')
        todo_luo = os.path.join(base,'todo_luo.xlsx')

        done_swahili = os.path.join(base,'done_swahili.xlsx')
        done_luo = os.path.join(base,'done_luo.xlsx')

        final = os.path.join(base,'translations.xlsx')

    def add_arguments(self,parser):
        # code.interact(local=locals())
        subparsers = parser.add_subparsers(help='sms bank commands')

        # The cmd argument is required for django.core.management.base.CommandParser
        check_parser = subparsers.add_parser('check',cmd=parser.cmd,help='print info for sms bank or translations')
        check_parser.add_argument('type',type=bank_or_translation,help='type of check. one of (b)ank or (t)anslation')
        check_parser.set_defaults(action='check_messages')

        make_parser = subparsers.add_parser('make',cmd=parser.cmd,help='make final translations or todos')
        make_parser.add_argument('type',type=todo_or_final,help='type of make. one of (t)do or (f)inal')
        make_parser.set_defaults(action='make_messages')

        clean_parser = subparsers.add_parser('clean',cmd=parser.cmd,help='clean messages bank or translations')
        clean_parser.add_argument('type',type=bank_or_translation,help='type of check. one of (b)ank or (t)anslation')
        clean_parser.set_defaults(action='clean_messages')

        import_parser = subparsers.add_parser('import',cmd=parser.cmd,help='import messages to backend')
        import_parser.add_argument('-d','--done',default=False,action='store_true',help='only import messages marked as done')
        import_parser.set_defaults(action='import_messages')

        test_parser = subparsers.add_parser('test',cmd=parser.cmd,help='test message row creation')
        test_parser.set_defaults(action='test')

        custom_parser = subparsers.add_parser('custom',cmd=parser.cmd,help='run custom command')
        custom_parser.set_defaults(action='custom')

    def handle(self,*args,**options):

        self.options = options
        getattr(self,options['action'])()

    ########################################
    # Commands
    ########################################

    def custom(self):
        sms_bank = xl.load_workbook(self.Paths.bank)
        new_wb = xl.workbook.workbook()
        ws = new_wb.active

        for row in sms_bank.get_sheet_by_name('anc').rows:
            if row[0].value == '#':
                ws.append(row)
            else:
                msg = sms.MessageBankRow(row)
                ws.append(msg.get_bank_row())

    def print_statistics(self):
        sms_bank = xl.load_workbook(self.options['bank'])
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

    def make_messages(self):
        if self.options.type == 'todo':
            self.make_todo_messages()
        elif self.options.type == 'final':
            self.make_final_messages()

    def make_todo_messages(self):

        sms_bank = xl.load_workbook(self.Paths.bank)
        old_translations = sms.message_dict(final_wb.active,sms.FinalRow)

        translations = read_sms_bank(sms_bank,old_translations,'anc','special')

        print "Total Found: {} Todo: {}".format( len(translations),
            len([t for t in translations if t.status == 'todo']) )

        swahili_wb = make_language_todos(translations,'swahili')
        luo_wb = make_language_todos(translations,'luo')

        swahili_wb.save(self.Paths.todo_swahili)
        luo_wb.save(self.Paths.todo_luo)

    def check_messages(self):

        if self.options['type'] == 'bank':
            sms_wb = xl.load_workbook(self.Paths.bank)
            messages = sms.read_sms_bank(sms_wb,None,'anc','special')
        elif self.options['type'] == 'translation':
            sms_wb = xl.load_workbook(self.Paths.final)
            messages = sms.parse_messages(sms_wb.active,sms.FinalRow)
        else:
            raise argparse.ArgumentTypeError('invalild type')

        stats = recursive_dd()
        for msg in messages:
            condition_hiv = stats[ '{}_HIV_{}'.format(msg.track,msg.get_hiv_messaging_str()) ]
            condition_hiv.default_factory = list

            base_group = condition_hiv[ '{}_{}'.format(msg.send_base,msg.group) ]
            base_group.append(msg)

        for condition_hiv, base_groups in stats.items():
            self.stdout.write( '{}'.format(condition_hiv) )
            for base_group,items in base_groups.items():
                count = len(items)
                todo = len(filter(lambda m: m.status == 'todo',items))
                self.stdout.write('\t{} {} ({})'.format(base_group,count,todo))

        # for base, groups in stats.items():
        #     for group, tracks in groups.items():
        #         for track, hiv_messaging in tracks.items():
        #             for hiv, count in hiv_messaging.items():
        #                 print "{}_{}_{}_{}: {}".format(base,group,track,hiv,count)

        # self.options['ascii_msg'] = 'Warning: non-ascii chars found: {count}'
        # non_ascii_dict = self.non_ascii_count()
        #
        # todo = argparse.Namespace(total=0,swahili=0,luo=0)
        # for row in sms_bank.active.rows[1:]:
        #     msg = sms.MessageRow(row,translation=True)
        #     if msg.status == 'todo':
        #         todo.total += 1
        #         todo.swahili += 1 if msg.swahili == '' else 0
        #         todo.luo += 1 if msg.luo == '' else 0
        #
        # print 'Check Complete: ToDo: {0.total} Swahili:{0.swahili} Luo: {0.luo} Diff: {1}'.format(todo,todo.total-todo.swahili-todo.luo)

    def process_messages(self):
        sms_bank = xl.load_workbook(self.options['bank'])
        old_translations = sms.message_dict(sms_bank.worksheets[0],translation=True)

        translations = xl.workbook.Workbook()
        new_ws = translations.active
        new_ws.append(sms.MessageRow.translation_header())

        todo_count = 0
        for row in sms_bank.active.rows[1:]:
            msg = sms.MessageRow(row,translation=True)
            if msg.status == 'done':
                msg.status = 'clean'
            elif msg.status == 'todo' and msg.new != '':
                msg.english = msg.new
            todo_count += msg.add_translation(new_ws,old_translations)

        print 'Todo:',todo_count
        new_ws.freeze_panes = 'A2'
        new_ws.auto_filter.ref = 'A1:K1'

        column_widths = {'A':4,'D':6,'E':6,'F':6,'G':45,'H':45,'I':45,'J':45}
        for col_letter, width in column_widths.items():
            new_ws.column_dimensions[col_letter].width = width

        translations.save('ignore/translations.xlsx')

    def import_messages(self):
        sms_bank = xl.load_workbook(self.Paths.final)
        do_all = not self.options.get('done',False)

        todo,total = 0,0
        for row in sms_bank.active.rows[1:]:
            msg = sms.FinalRow(row)
            total += 1
            if do_all or msg.status == 'done':
                auto = back.AutomatedMessage.objects.from_excel(msg)
                if msg.status == 'todo':
                    self.stdout.write('Warning: message {} still todo'.format(msg.description()))
                    todo += 1
        self.stdout.write('Messages Imported: {} Messages Todo: {}'.format(total,todo))

    def non_ascii_count(self):
        sms_bank = xl.load_workbook(self.options['bank'])
        non_ascii = collections.defaultdict(int)

        # Count non ascii characters (ord value greater than 127)
        for row in sms_bank.active.rows[1:]:
            msg = sms.MessageRow(row,translation=True)

            for c in msg.english + msg.swahili + msg.luo:
                if ord(c) > 127:
                    non_ascii[c] += 1

        # Print non ascii counts
        print self.options.get('ascii_msg','non-ascii count: {count}').format(count=len(non_ascii))
        for c,count in non_ascii.items():
            print u'({0!r} {0!s}) => {1}'.format(c,count)

        return len(non_ascii) > 0

    def test(self):

        final_wb = xl.load_workbook(self.Paths.final)
        old_translations = sms.message_dict(final_wb.active,sms.FinalRow)

        print 'Count: {} Example: {!r}'.format(len(old_translations),old_translations.get(old_translations.keys()[0]))



########################################
#  Utility Functions
########################################

WRAP_TEXT = xl.styles.Alignment(wrap_text=True,vertical='top')

def recursive_dd():
    return collections.defaultdict(recursive_dd)

def bank_or_translation(option):
    if option.startswith('b'):
        return 'bank'
    elif options.startswith('t'):
        return 'translation'
    raise argparse.ArgumentTypeError('type must be either bank or translation')

def todo_or_final(option):
    if option.startswith('t'):
        return 'todo'
    elif options.startswith('f'):
        return 'final'
    raise argparse.ArgumentTypeError('type must be either todo or translation')


def make_language_todos(translations,language):

    wb = xl.workbook.Workbook()
    ws = wb.active

    ws.append(sms.TranslationRow.header(language))

    for msg in translations:
        ws.append(msg.get_translation_row(language))
        last = ws.rows[-1]
        for i in [6,7,8]:
            last[i].alignment = WRAP_TEXT

    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = 'A1:I1'

    column_widths = {'A':4,'D':6,'E':6,'F':6,'G':50,'H':50,'I':50}
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    return wb
