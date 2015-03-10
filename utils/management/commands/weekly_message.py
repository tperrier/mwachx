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
    )

    def handle(self,*args,**options):

        delta = options['week']*7
        self.filename = options['file']
        self.verbosity = options['verbosity']

        today = datetime.date.today()
        self.start = today - datetime.timedelta(days=today.weekday()+8+delta)
        self.end = today - datetime.timedelta(days=today.weekday()+1+delta)
        self.messages = cont.Message.objects.filter(created__range=(self.start,self.end))

        if self.filename is None:
            self.filename = self.start.strftime('messages_%Y-%m-%d.xlsx')

        self.make_workbook()

    def make_workbook(self):
        print 'Making Workbook: %s for %s to %s with %i messages %i'%(self.filename,self.start,self.end,self.messages.count())

        wb = xl.Workbook()
        ws = wb.active
        ws.title = self.start.strftime('%Y-%m-%d')

        header = ('Date','Direction','Participant','Nurse','Facility','Message','Translation')
        ws.append(header)
        for msg in self.messages:
            ws.append((
                msg.created,
                'O' if msg.is_outgoing else 'D',
                str(msg.contact),
                str(msg.admin_user),
                str(msg.contact.facility) if msg.contact else None,
                msg.text,
                msg.translated_text
            ))

        wb.save(self.filename)
