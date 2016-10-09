#!/usr/bin/python
from optparse import make_option
import datetime, openpyxl as xl

from django.core.management.base import BaseCommand


import contacts.models as cont


class Command(BaseCommand):

    help = 'Generate an xlsx report of messages sent last week'
    option_list = BaseCommand.option_list + (
        make_option('-w','--week',type=int,help='number of weeks back',metavar='WEEKS',default=0),
        make_option('-f','--file',help='filename to save xlsx sheet as',metavar='FILE',default=None),
        make_option('--all',help='overide date range use all messages',action='store_true',default=False),
    )

    def handle(self,*args,**options):

        delta = options['week']*7
        self.filename = options['file']
        self.verbosity = options['verbosity']

        if not options['all']:
            today = datetime.date.today()
            self.start = today - datetime.timedelta(days=today.weekday()+8+delta)
            self.end = today - datetime.timedelta(days=today.weekday()+1+delta)
            self.messages = cont.Message.objects.filter(created__range=(self.start,self.end))
        else:
            self.start,self.end = None,None
            self.messages = cont.Message.objects.all()

        if self.filename is None:
            if self.start is not None:
                self.filename = self.start.strftime('messages_%Y-%m-%d.xlsx')
            else:
                self.filename = 'messages_all.xlsx'

        self.make_workbook()

    def make_workbook(self):
        if self.start is not None:
            print 'Making Workbook: %s for %s to %s messages %i'% \
                (self.filename,self.start,self.end,self.messages.count())
        else:
            print 'Making Workbook: %s with all (%i) messages'%(self.filename,self.messages.count())


        wb = xl.Workbook()

        ws = wb.active
        ws.title = 'Bondo'
        make_worksheet(ws,self.messages.filter(contact__facility='bondo'))

        ws = wb.create_sheet()
        ws.title = 'Mathare'
        make_worksheet(ws,self.messages.filter(contact__facility='mathare'))

        ws = wb.create_sheet()
        ws.title = 'Ahero'
        make_worksheet(ws,self.messages.filter(contact__facility='ahero'))

        ws = wb.create_sheet()
        ws.title = 'None'
        make_worksheet(ws,self.messages.filter(contact__isnull=True))


        wb.save(self.filename)

def make_worksheet(ws,messages):
    header = ('Date','Direction','Participant','Nurse','Facility','Message','Translation')
    ws.append(header)
    for msg in messages:
        ws.append((
            msg.created,
            'O' if msg.is_outgoing else 'D',
            str(msg.contact),
            str(msg.admin_user),
            str(msg.contact.facility) if msg.contact else None,
            msg.text,
            msg.translated_text
        ))
