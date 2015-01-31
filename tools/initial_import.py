#!/usr/bin/python
import json,datetime,sys,os,code,random

# Setup Django Environment
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(FILE_DIR)
print FILE_DIR
PROJECT_ROOT = os.path.join(FILE_DIR,'..')
sys.path.append(PROJECT_ROOT) #path to mWaCh

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','mwach.settings')
django.setup()
# End Django Setup 

from django.db.models import Max
import contacts.models as cont


###################
# Utility Functions
###################


study_groups = ['control','one-way','two-way']
def add_client(client,i):
    new_client = {
        'study_id':i,
        'anc_num':client['anc_num'],
        'nickname':client['nickname'],
        'birthdate':client['birth_date'],
        'study_group':random.choice(study_groups),
        'due_date':get_due_date(),
        'last_msg_client':client['last_msg_client'],
        }
    contact = cont.Contact.objects.create(**new_client)
    connection = cont.Connection.objects.create(identity=client['phone_number'],contact=contact,is_primary=True)
    
    for m in client['messages']:
        add_message(m,contact,connection)
    for v in client['visits']:
        add_visit(v,contact)
    for n in client['notes']:
        add_note(n,contact)
            
    return new_client
    
def add_message(message,contact,connection):
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
    
def add_visit(visit,contact):
    if visit['scheduled_date']:
        new_visit = {
            'scheduled':visit['scheduled_date'],
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

###################
# End Utility Functions
###################

JSON_DATA_FILE = 'small.json'
IMPORT_COUNT = 10
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

'''    
update contacts_message set is_viewed = 1 where id not in 
(select max(id) contacts_message where is_outgoing=0 group by contact_id); 
'''
