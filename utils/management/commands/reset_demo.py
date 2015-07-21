#!/usr/bin/python
import json,datetime,sys,os,code,random,collections
from optparse import make_option
import openpyxl as xl

#Django Imports
from django.contrib.auth.models import User
from django.db.models import Max
from django.core.management import ManagementUtility
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction 
from django.contrib.auth.models import User

from constance import config

import contacts.models as cont

class Command(BaseCommand):
    
    help = 'Delete and reset messages, contacts and visits for the Demo Site'

    option_list = BaseCommand.option_list + (
        make_option('-d','--dry-run',default=False,action='store_true',
            help='Do not make changes in database. Default: False'),
    )

    def handle(self,*args,**options):

        if options['dry_run']:
            print 'Dry Run: No database changes'
        else:
            print 'Live Run: Changing database'

        try:
            # Make sure demo facility exists 
            demo = cont.Facility.objects.get(name='demo')
            print 'Demo Facility Exists....Deleting'
            demo.delete()
            # Make sure participants exist 

        except cont.Facility.DoesNotExist:
            print 'Demo Facility Does Not Exist'

        if not options['dry_run']:
            demo = create_facility()
            cont.Practitioner.objects.create(user=User.objects.first(),facility=demo)

        excel_file = 'ignore/demo_messages.xlsx'
        if settings.ON_OPENSHIFT:
            excel_file = os.path.join(os.environ['OPENSHIFT_DATA_DIR'],'demo_messages.xlsx')

        clients,messages = load_excel(excel_file)

        if not options['dry_run']:
            # Returns {nickname => contact}
            contacts = create_participants(demo,clients)
            create_messages(contacts,messages)
            config.CURRENT_DATE = '2015-07-20'
        
######################################################################
# Utility Functions
######################################################################

### ****** Named Tuples ****** ###
# Headers: nickname, due_date, last_msg_client, status
Client = collections.namedtuple('Client',('nickname','due_date','last_msg_client','status','visit'))
#Headers: Dates,  Time, Sender,  Name Client, Message
Message = collections.namedtuple('Message',('created','is_system','is_outgoing','client','message'))

### ****** Functions to parse the Excel File ****** ###
def get_values(row):
    return [cell.value for cell in row]

def make_date(date_str):
    if date_str is not None:
        return datetime.datetime.strptime(date_str+'-2015','%d-%b-%Y').date()

def make_time(time_str):
    if time_str is not None:
        return datetime.datetime.strptime(time_str,'%I:%M %p').time()

def make_client(row):
    nickname,due_date,last_msg_client,status,visit = get_values(row[:5])
    return Client(nickname,make_date(due_date),make_date(last_msg_client),status,make_date(visit))

def make_message(row):
    date,time,sender,client,message = get_values(row[:5])
    print date,time,sender,client
    is_system = sender.startswith('S')
    is_outgoing = not sender.startswith('C')
    created = datetime.datetime.combine(make_date(date),time)
    return Message(created,is_system,is_outgoing,client,message)

def load_excel(file_name):
    wb = xl.load_workbook(file_name)
    client_ws = wb['Clients']
    message_ws = wb['Messages']
    clients = [make_client(row) for row in client_ws.rows[1:]]
    messages = [make_message(row) for row in message_ws.rows[1:]]
    return clients,messages


### ****** Functions to make database objects ****** ###
def create_facility():
    return cont.Facility.objects.create(name="demo")

def create_participants(facility,clients):
    contacts = {}
    for c in clients:
        contacts[c.nickname] = create_contact(facility,c)
    return contacts

def create_messages(contacts,messages):
    for m in messages:
        create_message(contacts[m.client],m)

def create_message(contact,message):
    new_message = {
        'text':message.message,
        'is_outgoing':message.is_outgoing,
        'is_system':message.is_system,
        'contact':contact,
        'connection':contact.connection,
        'translated_text':message.message,
        'translate_skipped':True,
    }
    if message.created < datetime.datetime(2015,7,1):
        new_message['is_viewed'] = True
    _message = cont.Message.objects.create(**new_message)
    _message.created = message.created
    _message.save()

def create_contact(facility,client):
    new_client = {
        'study_id':random.randint(10000,100000),
        'anc_num':random.randint(1000,10000),
        'nickname':client.nickname,
        'birthdate':datetime.date(1980,1,1),
        'study_group':'two-way',
        'due_date':client.due_date,
        'last_msg_client':client.last_msg_client,
        'facility':facility,
        'status':client.status,
    }

    contact = cont.Contact.objects.create(**new_client)
    connection = cont.Connection.objects.create(
        identity='+2500111{}'.format(new_client['anc_num']),
        contact=contact,
        is_primary=True)
    if client.visit:
        cont.Visit.objects.create(contact=contact,scheduled=client.visit,reminder_last_seen=client.visit)
    return contact