#!/usr/bin/python
import json,datetime,sys,os,code,random
import dateutil.parser

#Django Imports
from django.contrib.auth.models import User
from django.db.models import Max
import contacts.models as cont
from django.core.management import ManagementUtility
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction 

class Command(BaseCommand):
    
    help = 'Delete old sqlite file, migrate new models, and load fake data'
    
    def handle(self,*args,**options):

        #Delete old DB
        print 'Deleting old sqlite db....'
        if settings.ON_OPENSHIFT:
            os.remove(os.path.join(os.environ['OPENSHIFT_DATA_DIR'],'mwach.db'))
        else:
            os.remove(os.path.join(settings.PROJECT_PATH,'mwach.db'))
        
        #Migrate new models
        print 'Migrating new db....'
        utility = ManagementUtility(['initial_import.py','migrate'])
        utility.execute()
        
        #Turn off Autocommit 
        transaction.set_autocommit(False)
        
        #Add new fake data
        create_languages()
        create_facilities()
        create_users()
        
        JSON_DATA_FILE =  os.path.join(settings.PROJECT_ROOT,'tools','small.json')
        if settings.ON_OPENSHIFT:
            JSON_DATA_FILE = os.path.join(os.environ['OPENSHIFT_DATA_DIR'],'small.json')
        IMPORT_COUNT = 15
        clients = json.load(open(JSON_DATA_FILE))
        clients = clients.values()[:IMPORT_COUNT]

        for i,c in enumerate(clients):
            print add_client(c,i)

        #Mark the last message for each contact is_viewed=False
        last_messages = cont.Message.objects.filter(is_outgoing=False).values('contact_id').order_by().annotate(Max('id'))
        cont.Message.objects.exclude(id__in=[d['id__max'] for d in last_messages]).update(is_viewed=True)
        #Move the last message to the front of the message que
        for msg in cont.Message.objects.filter(id__in=[d['id__max'] for d in last_messages]):
            before_msg = msg.contact.message_set.all()[random.randint(1,3)]
            msg.created = before_msg.created + datetime.timedelta(seconds=600)
            msg.save()

        # Make last visit arrived = None.
        last_visits = cont.Visit.objects.all().values('contact_id').order_by().annotate(Max('id'))
        cont.Visit.objects.filter(id__in=[d['id__max'] for d in last_visits]).update(arrived=None,skipped=None)
        
        #commit data
        transaction.commit()
        
###################
# Utility Functions
###################

study_groups = ['control','one-way','two-way']
facility_list = cont.Facility.objects.exclude(name='kisumu_east')
def add_client(client,i):
    new_client = {
        'study_id':i,
        'anc_num':client['anc_num'],
        'nickname':client['nickname'],
        'birthdate':client['birth_date'],
        'study_group':random.choice(study_groups),
        'due_date':get_due_date(),
        'last_msg_client':client['last_msg_client'],
        'facility':facility_list[i%3],
        'status':'post' if random.random() < .25 else 'pregnant',
        }
    contact = cont.Contact.objects.create(**new_client)
    connection = cont.Connection.objects.create(identity='+'+client['phone_number'],contact=contact,is_primary=True)
    
    message_count = len(client['messages'])
    for i,m in enumerate(client['messages']):
        #only make translations for last five messages
        translate = i < message_count - 5
        add_message(m,contact,connection,translate)
    for v in client['visits']:
        add_visit(v,contact)
    for n in client['notes']:
        add_note(n,contact)
            
    return new_client

def add_message(message,contact,connection,translate=False):
    outgoing = message['sent_by'] != 'Client'
    system = message['sent_by'] == 'System'

    new_message = {
        'text':message['content'],
        'is_outgoing':outgoing,
        'is_system':system,
        'contact':contact,
        'connection':connection
    }
    _message = cont.Message.objects.create(**new_message)
    _message.created = message['date']

    if translate and not system:
        _message.translated_text = "(translated)" + message['content']
        _message.is_translated = True
        _lang = cont.Language.objects.get(id=random.randint(1,4))
        _message.languages.add(_lang)
    
    _message.save()
    
def add_visit(visit,contact):
    if visit['scheduled_date']:
        new_visit = {
            'scheduled':visit['scheduled_date'],
            'reminder_last_seen':dateutil.parser.parse(visit['scheduled_date'])-datetime.timedelta(days=1),
            'arrived':visit['date'],
            'skipped':True if random.random() < .25 else False,
            'comment':visit['comments'],
            'contact':contact
        }
        _visit = cont.Visit.objects.create(**new_visit)
        
def add_note(note,contact):
    new_note = {
        'contact':contact,
        'comment':note['content'],
    }
    
    _note = cont.Note.objects.create(**new_note)    
    _note.created = note['date']
    _note.save()
    
    
def get_due_date():
    return datetime.date.today() + datetime.timedelta(days=random.randint(0,100))

def create_languages():
    cont.Language.objects.bulk_create([
        cont.Language(**{"short_name":"E", "name": 'English'}),
        cont.Language(**{"short_name":"S", "name": 'Swahili'}),
        cont.Language(**{"short_name":"H", "name": 'Sheng'}),
        cont.Language(**{"short_name":"L", "name": 'Luo'}),
    ])
    
def create_facilities():
    cont.Facility.objects.bulk_create([
        cont.Facility(name='bondo'),
        cont.Facility(name='ahero'),
        cont.Facility(name='mathare'),
        cont.Facility(name='kisumu_east'),
    ])
    
def create_users():
    #create admin user
    oscard = User.objects.create_superuser('admin',email='o@o.org',password='mwachx')
    cont.Practitioner.objects.create(facility=cont.Facility.objects.get(pk=1),user=oscard)
    #create study nurse users
    facility_list = ['bondo','ahero','mathare']
    for f in facility_list:
        user = User.objects.create_user('n_{}'.format(f),password='mwachx')
        cont.Practitioner.objects.create(facility=cont.Facility.objects.get(name=f),user=user)
