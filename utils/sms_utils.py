#!/usr/bin/python
import code
import operator, collections, re, itertools

class MessageRowBase(object):

    def __init__(self,row,status,group,track,hiv,send_base,offset,english,swahili,luo,**kwargs):
        self.group, self.track, self.hiv = group, track, hiv
        self.send_base, self.offset = send_base, offset
        self.english, self.swahili, self.luo, = map(clean_msg,(english,swahili,luo))

        self.comment = kwargs.get('comment','')
        if self.comment is None:
            self.comment = ''
            
        self.new = kwargs.get('new','')
        self.row = row[0].row

        if any( [s is None for s in group,track,hiv,send_base,offset ] ):
            status = '#'
        self.set_status(status)

        if self.status != 'comment':
            self.group = self.group.replace('_','-')
            self.configure_variables()
            self.set_hiv_messaging()

            if self.offset is None:
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
                'todo':self.is_todo()}

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

    def set_status(self,status):
        if status is None:
            self.status =  'clean'
        else:
            self.status =  {'':'clean','x':'done','s':'swahili','l':'luo','!':'todo','#':'comment'}.get(status.lower()[0],'clean')

    def get_status_str(self):
        return {'clean':'','done':'x','todo':'!','comment':'#','swahili':'s','luo':'l'}.get(self.status,'')

    def is_todo(self):
        return self.status in ['todo','swahili','luo']

    def set_hiv_messaging(self):
        if isinstance(self.hiv,basestring):
            self.hiv = self.hiv.strip().lower().startswith('y')
        else:
            self.hiv = bool(self.hiv)

    def get_hiv_messaging_str(self):
        return 'Y' if self.hiv else 'N'

    def configure_variables(self):
        self.english = replace_vars(self.english)

        if self.english.startswith('{name}, this is {nurse} from {clinic}'):
            if not self.swahili.startswith('{name},'):
                self.swahili = '{name}, huyu ni {nurse} kutoka {clinic}. ' + self.swahili
            if not self.luo.startswith('{name},'):
                self.luo = '{name}, mae en {nurse} mawuok {clinic}.' + self.luo

    def __repr__(self):
        return self.description()

    def get_translation_row(self,language):
        return (
            '!' if self.is_todo() and self.status != language else '',
            self.group,
            self.track,
            self.get_hiv_messaging_str(),
            self.send_base,
            self.offset,
            self.english,
            self.new if self.status != language else '',
            self.swahili if language == 'swahili' else self.luo
        )

    def get_final_row(self):
        return (
            self.get_status_str(),
            self.group,
            self.track,
            self.get_hiv_messaging_str(),
            self.send_base,
            self.offset,
            self.english,
            self.swahili,
            self.luo,
            self.comment
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
        super(FinalRow,self).__init__(row,status,group,track,hiv,send_base,offset,
            english,swahili,luo,comment=comment)

        # If message is translated make old equal new
        if self.status == 'done':
            self.status = 'clean'

class MessageBankRow(MessageRowBase):

    def __init__(self,row,old_translations=None):
        status, group, track, hiv, send_base, offset, english, comment= \
            cell_values( *operator.itemgetter(0,1,2,3,4,5,6,8)(row))
        swahili , luo = '' , ''
        super(MessageBankRow,self).__init__(row,status,group,track,hiv,send_base,offset,
            english,swahili,luo,comment=comment)

        self.set_old(old_translations)


    def set_old(self,old_translations=None):

        if old_translations is None:
            return

        old = old_translations.get(self.description())
        if self.to_translate(old):
            self.new = self.english
            self.english = old.english if old is not None else ''
            self.status = old.status if old is not None and old.is_todo() else 'todo'

        if old is None:
            return

        self.swahili = old.swahili
        self.luo = old.luo


    def to_translate(self,old):
        if old is None or \
           (old.english != self.english and self.status != 'done') or \
           old.is_todo() or old.swahili == '' or old.luo == '':
            return True

class TranslationRow(MessageRowBase):

    @classmethod
    def header(cls,language):
        return ('Todo','Group','Track','HIV','Base','Offset','Old','New',language)

    def __init__(self,row,language_name):
        status, group, track, hiv, send_base, offset, english, new, language = \
            cell_values( *operator.itemgetter(0,1,2,3,4,5,6,7,8)(row))

        language_name = language_name.lower()[0]
        if language_name == 's':
            swahili = language
            luo = ''
        elif language_name == 'l':
            swahili = ''
            luo = language

        super(TranslationRow,self).__init__(row,status,group,track,hiv,send_base,offset,
            english,swahili,luo,new=new)


########################################
# Utility Functions
########################################

def parse_messages(ws,cls,**kwargs):
    for row in ws.rows:
        msg = cls(row,**kwargs)
        if msg.is_valid():
            yield msg

def read_sms_bank(bank,old=None,*args):
    return filter(lambda msg: msg.is_valid(), [
        MessageBankRow(row,old)
        for row in itertools.chain(
            *[bank.get_sheet_by_name(sheet).rows[1:] for sheet in args]
        )
    ])

def message_dict(ws,cls,**kwargs):
    messages = collections.OrderedDict()
    for msg in parse_messages(ws,cls,**kwargs):
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

def replace_vars(msg):
    if '<' in msg:
        variables = [
            ('<participant name>','{name}'),
            ('<nurse name>','{nurse}'),
            ('<clinic name>','{clinic}'),
        ]
        for needle,string in variables:
            msg = msg.replace(needle,string)
    return msg
