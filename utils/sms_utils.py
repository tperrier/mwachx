#!/usr/bin/python
import code
import operator, collections, re, itertools

class MessageRowBase(object):

    def __init__(self,row,status,group,track,hiv,send_base,offset,english,swahili,luo,comment):
        self.status, self.group, self.track, self.hiv = status, group, track, hiv
        self.send_base, self.offset = send_base, offset
        self.english, self.swahili, self.luo, self.comment = map(clean_msg,(english,swahili,luo,comment))
        self.new = ''

        self.row = row[0].row
        self.set_status()
        self.group = self.group.replace('_','-')
        self.configure_variables()
        self.set_hiv_messaging()

        if self.offset is None and self.status != 'comment':
            self.offset = self.get_offset()


    def description(self):
        ''' Return base_group_track_hiv_offset '''
        return "{0.send_base}.{0.group}.{0.track}.{1}.{0.offset}".format(
            self, self.get_hiv_messaging_str())

    def kwargs(self):
        return {'send_base':self.send_base,'send_offset':self.offset,'group':self.group,
                'condition':self.track,'comment':self.comment,'hiv_messaging':self.hiv,
                'english':self.english if self.english != '' else self.new,
                'swahili':self.swahili,'luo':self.luo,
                'todo':self.status == 'todo'}

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
            print 'Comment Warning: {} row {}'.format(self.comment,self.row)
            return None
        return int(match.group(0))

    def is_valid(self):
        if self.status == 'comment':
            return False
        group_valid = self.group in ['one-way','two-way','control']
        has_offset = self.offset is not None
        return group_valid and has_offset

    def set_status(self):
        if self.status is None:
            self.status = 'clean'
        elif self.status.lower() == 'x':
            self.status =  'done'
        elif self.status == '!':
            self.status = 'todo'
        elif self.status == '#':
            self.status = 'comment'
        else:
            self.status = 'clean'

    def get_status_str(self):
        return {'clean':'','done':'x','todo':'!','comment':'#'}.get(self.status,'')

    def set_hiv_messaging(self):
        if isinstance(self.hiv,basestring):
            self.hiv = self.hiv.strip().lower().startswith('y')
        else:
            self.hiv = bool(self.hiv)

    def get_hiv_messaging_str(self):
        return 'Y' if self.hiv else 'N'

    def configure_variables(self):
        if '<' in self.english:
            variables = [
                ('<participant name>','{name}'),
                ('<nurse name>','{nurse}'),
                ('<clinic name>','{clinic}'),
            ]
            for needle,string in variables:
                self.english = self.english.replace(needle,string)

        if self.english.startswith('{name}'):
            if not self.swahili.startswith('{name}'):
                self.swahili = '{name} huyu ni {nurse} kutoka {clinic} ' + self.swahili
            if not self.luo.startswith('{name}'):
                self.luo = '{name}, mae en {nurse} mawuok {clinic} ' + self.luo

    def __repr__(self):
        return self.description()

    def get_translation_row(self,language):
        return (
            self.get_status_str(),
            self.group,
            self.track,
            self.get_hiv_messaging_str(),
            self.send_base,
            self.offset,
            self.english,
            self.new,
            self.swahili if language == 'swahili' else self.luo
        )

    @classmethod
    def from_bank_row(cls,row):
        status, group, track, hiv, send_base, offset, english, comment= \
            cell_values( *operator.itemgetter(0,1,2,3,4,5,6,8)(row))

class FinalRow(MessageRowBase):

    header = ('Todo','Group','Track','HIV','Base','Offset','English','Swahili','Luo','Comment')

    def __init__(self,row):
        status, group, track, hiv, send_base, offset, english, swahili, luo, comment= \
            cell_values( *operator.itemgetter(0,1,2,3,4,5,6,7,8,9)(row))
        super(FinalRow,self).__init__(row,status,group,track,hiv,send_base,offset,english,swahili,luo,comment)

        # If message is translated make old equal new
        if self.status == 'done' and self.new != '':
            self.english = self.new
            self.new = ''
            self.status = 'clean'

class MessageBankRow(MessageRowBase):

    def __init__(self,row,old_translations=None):
        status, group, track, hiv, send_base, offset, english, comment= \
            cell_values( *operator.itemgetter(0,1,2,3,4,5,6,8)(row))
        swahili,luo = '',''
        super(MessageBankRow,self).__init__(row,status,group,track,hiv,send_base,offset,english,swahili,luo,comment)

        if old_translations is not None:
            old = old_translations.get(self.description())
            if self.to_translate(old):
                self.new = self.english
                self.english = old.english if old is not None else ''
                self.swahili = old.swahili if old is not None else ''
                self.luo = old.luo if old is not None else ''
                self.status = 'todo'

    def to_translate(self,old):
        if old is None or old.english != self.english or \
           old.status == 'todo' or self.status == 'todo' or \
           old.swahili == '' or old.luo == '':
            return True

    def make_translation(self,old_translations):
        old = old_translations.get(self.description())
        old_english = old.english if old is not None else ''
        new_english = self.english if self.to_translate(old) else ''
        return (self.get_to_translate_str(old),self.group, self.track, 'yes' if self.hiv else 'no', self.send_base,
            self.offset, old_english, new_english,
            old.swahili if old is not None else '',
            old.luo if old is not None else '',
            self.comment)

    def add_translation(self,ws,old_translations):
        if self.is_valid():
            row = self.make_translation(old_translations)
            ws.append(row)
            last = ws.rows[-1]
            last[6].alignment, last[7].alignment, last[8].alignment, last[9].alignment = WRAP_TEXT, WRAP_TEXT, WRAP_TEXT, WRAP_TEXT
            return 1 if row[0] == '!' else 0
        return 0

class TranslationRow(MessageRowBase):

    @classmethod
    def header(cls,language):
        return ('Todo','Group','Track','HIV','Base','Offset','Old','New',language)


########################################
# Utility Functions
########################################

def parse_messages(rows,cls):
    return filter(lambda r: r.is_valid(), [cls(r) for r in rows] )

def read_sms_bank(bank,old=None,*args):
    return filter(lambda x: x.is_valid(), [
        MessageBankRow(row,old)
        for row in itertools.chain(
            *[bank.get_sheet_by_name(sheet).rows[1:] for sheet in args]
        )
    ])

def message_dict(ws,cls):
    messages = collections.OrderedDict()
    for msg in parse_messages(ws,cls):
        messages[msg.description()] = msg
    return messages

def cell_values(*args):
    if len(args) == 1:
        return args[0].value
    return [arg.value for arg in args]

multiple_whitespace = re.compile(r'\s{2,}',re.M)
def clean_msg(msg):
    if not isinstance(msg,basestring):
        return ''
    msg = msg.replace(u'\u2019','\'')  # replace right quot
    msg = msg.replace(u'\xa0',' ') # replace non blank space
    msg = msg.strip()
    msg = msg.replace('\n',' ')
    msg = multiple_whitespace.sub(r' ',msg)
    return msg.replace('\n',' ')
