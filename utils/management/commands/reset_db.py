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

class Command(BaseCommand):
    
    help = 'Delete old sqlite file, migrate new models, and load fake data'
    
    def handle(self,*args,**options):
        
        #Delete old DB
        print 'Deleting old sqlite db....'
        os.remove(os.path.join(settings.PROJECT_PATH,'mwach.db'))
        
        #Migrate new models
        print 'Migrating new db....'
        utility = ManagementUtility(['initial_import.py','migrate'])
        utility.execute()
        
        #Add new fake data
        
        create_languages()
        create_facilities()
        create_users()
        
        JSON_DATA_FILE =  os.path.join(settings.PROJECT_ROOT,'tools','small.json')
        IMPORT_COUNT = 15
        clients = json.load(open(JSON_DATA_FILE))
        clients = random.sample(clients.values(),IMPORT_COUNT)

        for i,c in enumerate(clients):
            print add_client(c,i)

        #Make the last message for each contact is_viewed=False
        last_messages = cont.Message.objects.filter(is_outgoing=False).values('contact_id').order_by().annotate(Max('id'))
        cont.Message.objects.exclude(id__in=[d['id__max'] for d in last_messages]).update(is_viewed=True)

        # Make last visit arrived = None.
        last_visits = cont.Visit.objects.all().values('contact_id').order_by().annotate(Max('id'))
        cont.Visit.objects.filter(id__in=[d['id__max'] for d in last_visits]).update(arrived=None,skipped=None)
        
        
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
    connection = cont.Connection.objects.create(identity=client['phone_number'],contact=contact,is_primary=True)
    
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
    _message.save()

    mylang = cont.Language.objects.get(id=random.randint(1,4))
    mylang.messages.add(_message)
    mylang.save()

    if translate:
        new_translation = {
            'text':message['content'],
            'is_complete':True,
            'parent': _message,
        }
        _trans = cont.Translation.objects.create(**new_translation)
        _message.translation = _trans
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
    cont.Language.objects.create(**{"short_name":"E", "name": 'English'})
    cont.Language.objects.create(**{"short_name":"S", "name": 'Swahili'})
    cont.Language.objects.create(**{"short_name":"H", "name": 'Sheng'})
    cont.Language.objects.create(**{"short_name":"L", "name": 'Luo'})
    
def create_facilities():
    cont.Facility.objects.create(name='bondo')
    cont.Facility.objects.create(name='ahero')
    cont.Facility.objects.create(name='mathare')
    cont.Facility.objects.create(name='kisumu_east')
    
def create_users():
    #create admin user
    oscard = User.objects.create_superuser('admin',email='o@o.org',password='mwachx')
    cont.Practitioner.objects.create(facility=cont.Facility.objects.get(pk=1),user=oscard)
    #create study nurse users
    facility_list = ['bondo','ahero','mathare']
    for f in facility_list:
        user = User.objects.create_user('n_{}'.format(f),password='mwachx')
        cont.Practitioner.objects.create(facility=cont.Facility.objects.get(name=f),user=user)
