#!/usr/bin/python
import code
import operator, collections, re

class MessageRow(object):

    def __init__(self,row,translation=False):
        self.todo, self.group, self.track, self.hiv, self.send_base, self.offset, self.english = \
            cell_values( *operator.itemgetter(0,1,2,3,4,5,6)(row))
        self.english = clean_msg(self.english)

        if not translation:
            self.swahili = ''
            self.luo = ''
            self.comment = row[8].value
        else:
            self.swahili, self.luo, self.comment = \
                cell_values( *operator.itemgetter(7,8,9)(row))
            self.swahili = clean_msg(self.swahili)
            self.luo = clean_msg(self.luo)

        if self.hiv is not None:
            self.hiv = False if self.hiv.strip().lower().startswith('n')  else True
        if self.offset is None:
            self.offset = self.get_offset()

        self.row = row[0].row

    def description(self):
        ''' Return base_group_track_hiv_offset '''
        return "{0.send_base}_{0.group}_{0.track}_{1}_{0.offset}".format(
            self, 'Y' if self.hiv else 'N')

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
        if self.todo == '#':
            return False
        group_valid = self.group in ['one_way','two_way','control']
        has_offset = self.offset is not None
        return group_valid and has_offset

    def to_translate(self,old):
        global I
        if old is None or old.todo == '!':
            return '!'
        if old.swahili == '' or old.luo == '':
            return '!'
        if old.english.strip() != self.english.strip():
            print old.english.strip(), len(old.english.strip()), len(self.english.strip())

        return '' if old.english.strip() == self.english.strip() else '!'

    def make_row(self,row):
        row = cell_values(*row)
        if self.is_valid():
            row[5] = self.offset
        else:
            row[0] = '#'
        return row

    def make_translation(self,old_translations):
        old = old_translations.get(self.description())
        old_english = old.english if old is not None else ''
        new_english = self.english if old is None or old.english != self.english else ''
        return (self.to_translate(old),self.group, self.track, 'yes' if self.hiv else 'no', self.send_base,
            self.offset, old_english, new_english,
            old.swahili if old is not None else '',
            old.luo if old is not None else '',
            self.comment)

    @classmethod
    def translation_header(cls):
        return ('Todo','Group','Track','HIV','Base','Offset','Old','New','Swahili','Luo','Comment')

########################################
# Utility Functions
########################################

def parse_messages(ws,translation=False):
    messages = []
    for row in ws.rows[1:]:
        msg = MessageRow(row,translation)
        if msg.is_valid():
            messages.append(msg)
        else:
            print 'Row {} invalid: {}'.format(msg.row,msg)
    return messages

def message_dict(ws,translation=False):
    messages = collections.OrderedDict()
    for msg in parse_messages(ws,translation):
        messages[msg.description()] = msg
    return messages

def cell_values(*args):
    if len(args) == 1:
        return args[0].value
    return [arg.value for arg in args]

end_sentance = re.compile(r'([.?!])\s+',re.M)
def clean_msg(msg):
    if not isinstance(msg,basestring):
        return ''
    msg = end_sentance.sub(r'\1 ',msg.strip())
    return msg.replace('\n',' ')
