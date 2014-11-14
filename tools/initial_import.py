#!/usr/bin/python
import json,datetime,sys,os,code,random

# Setup Django Environment
FILE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.join(FILE_DIR,'..')
sys.path.append(PROJECT_ROOT) #path to mWaCh

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','mwach.settings')
django.setup()
# End Django Setup 

import contacts.models as cont


###################
# Utility Functions
###################

def get_messages(client):
    client_id = client['pk']
    interactions = get_interactions(client)

    client_messages = []
    for i in interactions:
        message = get_message(i)
        if message:
            client_messages.append( dict(i['fields'].items() + message['fields'].items() ) )

    return client_messages
    
def get_interactions(client):
    return [i for i in data['interaction'] if i['fields']['client_id'] == client['pk']]
    
def get_message(interaction):
    for m in data['message']:
        if m['pk'] == interaction['pk']:
            return m
    return None

study_groups = ['control','one-way','two-way']
def add_client(client,i):
    new_client = {
        'study_id':i,
        'anc_num':i,
        'first_name':client['fields']['first_name'],
        'last_name':client['fields']['last_name'],
        'nick_name':client['fields']['nickname'],
        'birth_date':client['fields']['birth_date'],
        'study_group':random.choice(study_groups),
        'due_date':get_due_date(),
        }
    contact = cont.Contact.objects.create(**new_client)
    connection = cont.Connection.objects.create(identity=random.randint(10000,1000000),contact=contact)
    for m in get_messages(client):
        add_message(m,contact,connection)
    return new_client
    
def add_message(message,contact,connection):
    outgoing = True if random.random() < 0.5 else False
    system = False if not outgoing else True if random.random() < 0.66 else False
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
    
    
def get_due_date():
    return datetime.date.today() + datetime.timedelta(days=random.randint(0,100))

###################
# End Utility Functions
###################

JSON_DATA_FILE = 'last_backup.json'

json_data = json.load(open(JSON_DATA_FILE))
data = {}
for d in json_data:
    try:
        data[d['model'][9:]].append(d)
    except KeyError as e:
        data[d['model'][9:]] = [d]
        
clients = random.sample(data['client'],10)

for i,c in enumerate(clients):
    print add_client(c,i)

