#!/usr/bin/python
import datetime, openpyxl as xl, os
from argparse import Namespace
import code
import operator, collections, re, argparse

from django.core.management.base import BaseCommand, CommandError
import utils.sms_utils as sms
import backend.models as back
import contacts.models as cont

class Command(BaseCommand):

    help = 'Parse and import SMS data bank'

    def add_arguments(self,parser):
        # code.interact(local=locals())
        parser.add_argument('-d','--dir',help='directory to find translations in default (translations)',default='translations')
        parser.add_argument('-f','--final',help='final xlsx name (translations.xlsx)',default='translations.xlsx')
        subparsers = parser.add_subparsers(help='sms bank commands')

        # The cmd argument is required for django.core.management.base.CommandParser
        make_parser = subparsers.add_parser('make',cmd=parser.cmd,help='make final translations or todos')
        make_parser.add_argument('type',type=todo_or_final,help='type of make. one of (t)do or (f)inal')
        make_parser.add_argument('--copy',help='make copy of todo messages',action='store_true',default=False)
        make_parser.add_argument('-c','--check',help='check final messages',action='store_true',default=False)
        make_parser.set_defaults(action='make_messages')

        check_parser = subparsers.add_parser('check',cmd=parser.cmd,help='check and print stats for final translations')
        check_parser.set_defaults(action='check_messages')

        clean_parser = subparsers.add_parser('clean',cmd=parser.cmd,help='clean messages bank')
        clean_parser.set_defaults(action='clean_messages')

        import_parser = subparsers.add_parser('import',cmd=parser.cmd,help='import messages to backend')
        import_parser.add_argument('-d','--done',default=False,action='store_true',help='only import messages marked as done')
        import_parser.add_argument('--clear',default=False,action='store_true',help='clear all existing backend messages')
        import_parser.add_argument('-f','--file',help='location of translation xlsx (default translations/translations.xlsx')
        import_parser.set_defaults(action='import_messages')

        participant_parser = subparsers.add_parser('part',cmd=parser.cmd,help='try to find messages for all current participants')
        participant_parser.set_defaults(action='test_participants')

        test_parser = subparsers.add_parser('test',cmd=parser.cmd,help='test message row creation')
        test_parser.set_defaults(action='test')

        custom_parser = subparsers.add_parser('custom',cmd=parser.cmd,help='run custom command')
        custom_parser.set_defaults(action='custom')

    def handle(self,*args,**options):

        self.stdout.write( 'Action: {} Root: {}'.format(options['action'],options['dir']) )

        self.paths = argparse.Namespace(
            bank = os.path.join(options['dir'],'bank.xlsx'),

            todo_swahili = os.path.join(options['dir'],'todo_swahili.xlsx'),
            todo_luo = os.path.join(options['dir'],'todo_luo.xlsx'),

            done_swahili = os.path.join(options['dir'],'done_swahili.xlsx'),
            done_luo = os.path.join(options['dir'],'done_luo.xlsx'),

            final = os.path.join(options['dir'],options['final'])
        )

        self.options = options
        getattr(self,options['action'])()

    ########################################
    # Commands
    ########################################

    def custom(self):
        sms_bank = xl.load_workbook(self.paths.final)

        counts = collections.defaultdict(int)
        for row in sms_bank.active.rows[1:]:
            msg = sms.FinalRow(row)
            counts[msg.track] += 1

        for track , count in counts.items():
            print track, count, len(track)


    def make_messages(self):
        self.stdout.write( 'Making Messages: {}'.format(self.options['type'].capitalize()) )
        if self.options['type'] == 'todo':
            self.make_todo_messages()
        elif self.options['type'] == 'final':
            self.make_final_messages()

    def make_todo_messages(self):
        ''' Take a formated SMS bank and create language specific todo files'''
        sms_bank = xl.load_workbook(self.paths.bank)
        try:
            final_wb = xl.load_workbook(self.paths.final)
            old_translations = sms.message_dict(final_wb.active,sms.FinalRow)
        except IOError as e:
            old_translations = None

        translations = sms.read_sms_bank(sms_bank,old_translations,'anc','postpartum','visits','special')

        print "Total Found: {} Todo: {}".format( len(translations),
            len([t for t in translations if t.is_todo()]) )

        swahili_wb = make_language_todos(translations,'swahili')
        luo_wb = make_language_todos(translations,'luo')

        swahili_wb.save(self.paths.todo_swahili)
        luo_wb.save(self.paths.todo_luo)

        if self.options['copy']:
            swahili_copy_path = path_with_date(self.paths.todo_swahili)
            luo_copy_path = path_with_date(self.paths.todo_luo)
            swahili_wb.save(swahili_copy_path)
            luo_wb.save(luo_copy_path)

    def make_final_messages(self):
        '''Take language specific todo files and done files and make a final translations file '''

        # Load todo messages or fail
        try:
            todo_swahili_wb = xl.load_workbook(self.paths.todo_swahili)
            todo_luo_wb = xl.load_workbook(self.paths.todo_luo)
        except IOError as e:
            self.stderr.write('Error: Swahili and or Lue todo files not found')
            return

        todo_swahili_bank = sms.message_dict(todo_swahili_wb.active,sms.TranslationRow,language_name='swahili')
        todo_luo_bank = sms.message_dict(todo_luo_wb.active,sms.TranslationRow,language_name='luo')

        # Load done messages or fail
        try:
            done_swahili_wb = xl.load_workbook(self.paths.done_swahili)
            done_luo_wb = xl.load_workbook(self.paths.done_luo)
        except IOError as e:
            self.stderr.write('Error: Swahili and or Lue done files not found')
            return
        done_swahili_bank = sms.message_dict(done_swahili_wb.active,sms.TranslationRow,language_name='swahili')
        done_luo_bank = sms.message_dict(done_luo_wb.active,sms.TranslationRow,language_name='luo')

        # Load sms bank
        sms_bank = xl.load_workbook(self.paths.bank)
        translations = sms.read_sms_bank(sms_bank,None,'anc','postpartum','visits','special')

        # Create final wb and add header
        final_wb = xl.workbook.Workbook()
        new_ws = final_wb.active
        new_ws.append(sms.FinalRow.header)

        for msg in translations:
            description = msg.description()

            todo_swahili , todo_luo = todo_swahili_bank[description] , todo_luo_bank[description]
            done_swahili , done_luo = done_swahili_bank[description] , done_luo_bank[description]
            msg.swahili , msg.luo , msg.english = done_swahili.swahili , done_luo.luo , msg.english

            # Determine done status
            is_done_swahili = not done_swahili.is_todo() or todo_swahili.swahili != done_swahili.swahili
            is_done_luo = not done_luo.is_todo() or todo_luo.luo != done_luo.luo
            if not ( done_luo.is_todo() and done_swahili.is_todo() ):
                msg.status = 'clean'
            elif is_done_swahili and is_done_luo:
                msg.status = 'done'
            elif is_done_swahili:
                msg.status = 'swahili'
            elif is_done_luo:
                msg.status = 'luo'
            else:
                msg.status = 'todo'

            msg.configure_variables()
            new_ws.append(msg.get_final_row())

            # Wrap text on english, swahili, luo columns
            last = new_ws.rows[-1]
            for i in [6,7,8]:
                last[i].alignment = WRAP_TEXT

            new_ws.freeze_panes = 'A2'
            new_ws.auto_filter.ref = 'A1:I1'

            column_widths = {'A':4,'D':6,'E':6,'F':6,'G':50,'H':50,'I':50}
            for col_letter, width in column_widths.items():
                new_ws.column_dimensions[col_letter].width = width


        final_wb.save(self.paths.final)

        if self.options['check']:
            self.check_messages()
        else:
            self.stdout.write('{} translations. {} todo.'.format( len(translations),
                len([m for m in translations if m.is_todo()])
            ) )


    def check_messages(self):
        ''' Check Final Translations
            report base_group
                track_HIV (count) [offset]
        '''
        sms_wb = xl.load_workbook(self.paths.final)
        messages = sms.parse_messages(sms_wb.active,sms.FinalRow)

        stats = recursive_dd()
        descriptions = set()
        duplicates = []
        total = 0
        for msg in messages:
            total += 1
            base_group = stats[ '{}_{}'.format(msg.send_base,msg.group) ]
            base_group.default_factory = list

            condition_hiv = base_group[ '{}_HIV_{}'.format(msg.track,msg.get_hiv_messaging_str()) ]
            condition_hiv.append(msg)

            description = msg.description()
            if description not in descriptions:
                descriptions.add(description)
            else:
                duplicates.append(description)

        for base_group, condition_hiv_groups in stats.items():
            self.stdout.write( '{}'.format(base_group) )
            for condition_hiv, items in condition_hiv_groups.items():
                self.stdout.write( '\t{}: {}'.format( condition_hiv, len(items) ) )
                offsets = ["{0: 3}".format(i) for i in sorted([i.offset for i in items]) ]
                for i in range( len(offsets)/10 + 1 ):
                    self.stdout.write( "\t\t{}".format( "".join(offsets[15*i:15*(i+1)]) ) )
        self.stdout.write( 'Total: {} Todo: {}'.format( total,
            len([m for m in messages if m.is_todo()])
        ) )

        if duplicates:
            for d in duplicates:
                self.stdout.write( 'Duplicate: {}'.format(d) )
        else:
            self.stdout.write(' No Duplicates ')

        # self.options['ascii_msg'] = 'Warning: non-ascii chars found: {count}'
        # non_ascii_dict = self.non_ascii_count()
        #

    def clean_messages(self):
        sms_bank = xl.load_workbook(self.paths.bank)
        for ws in sms_bank.worksheets:
            self.clean_sheet(ws)
        sms_bank.save(os.path.join(self.options['dir'],'new_bank.xlsx'))

    def clean_sheet(self,ws):
        self.stdout.write( "Cleaning Sheet: {}".format(ws.title) )
        for row in ws.rows[1:]:
            self.clean_cell(row[6])

    def clean_cell(self,cell):
        cleaned = sms.clean_msg(cell.value)
        cell.value = sms.replace_vars(cleaned)

    def import_messages(self):
        sms_bank_file = self.paths.final if self.options['file'] is None else self.options['file']
        sms_bank = xl.load_workbook(sms_bank_file)
        messages = sms.parse_messages(sms_bank.active,sms.FinalRow)

        clear = self.options.get('clear')
        do_all = not self.options.get('done') or clear

        if clear:
            self.stdout.write('Deleting All Backend Messages')
            back.AutomatedMessage.objects.all().delete()

        self.stdout.write('Importing....')
        total , add , todo, create = 0 , 0 , 0 , 0
        counts = collections.defaultdict(int)
        diff , existing = [] , []
        for msg in messages:
            counts['total'] += 1

            if do_all or msg.status == 'done':
                auto , status = back.AutomatedMessage.objects.from_excel(msg)
                counts['add'] += 1
                counts[status] += 1

                if status != 'created':
                    existing.append( (msg,auto) )
                if status == 'changed':
                    diff.append( (msg,auto) )

                if msg.is_todo():
                    self.stdout.write('Warning: message {} still todo'.format(msg.description()))
                    counts['todo'] += 1

        self.stdout.write('Messages Found: {0[total]} Imported: {0[add]} Created: {0[created]} Changed: {0[changed]} Todo: {0[todo]}'.format(counts))

        if clear:
            if existing:
                self.stdout.write( 'Existing:')
                for e in existing:
                    self.stdout.write( '\t{0[0]} - {0[1]}'.format(e) )
            else:
                self.stdout.write( 'Existing: None')

        if diff:
            self.stdout.write( 'Different:')
            for d in diff:
                self.stdout.write( '\t{0[0]} - {0[1]}'.format(d) )
        else:
            self.stdout.write( 'Different: None')




    def test_participants(self):

        found , missing = 0 , []
        for c in cont.Contact.objects.exclude(study_group='control'):
            auto = back.AutomatedMessage.objects.from_description( c.description() )
            if auto is None:
                missing.append(c)
            else:
                found += 1

        self.stdout.write( "Total: {} Found: {} Missing: {}".format( found + len(missing), found, len(missing) ) )

        if missing:
            self.stdout.write( "Missing Participants:" )
            for m in missing:
                self.stdout.write( "\t{!r} {}".format(m,m.description()) )
        else:
            self.stdout.write( "Missing Participants: 0" )

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

        final_wb = xl.load_workbook(self.paths.final)
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
    elif option.startswith('f'):
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

def path_with_date(path):
    root , ext = os.path.splitext(path)
    date_str = datetime.date.today().strftime('%Y-%m-%d')
    return "{}_{}{}".format(root,date_str,ext)
