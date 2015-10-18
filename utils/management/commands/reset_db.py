#!/usr/bin/python
import json,datetime,sys,os,code,random
import dateutil.parser
from optparse import make_option

#Django Imports
from django.contrib.auth.models import User
from django.db.models import Max
from django.core.management import ManagementUtility
from django.core.management.base import BaseCommand
from django.conf import settings
from constance import config
from django.db import transaction

import contacts.models as cont
import utils

JSON_DATA_FILE =  os.path.join(settings.PROJECT_ROOT,'tools','small.json')
if settings.ON_OPENSHIFT:
    JSON_DATA_FILE = os.path.join(os.environ['OPENSHIFT_DATA_DIR'],'small.json')

class Command(BaseCommand):

    help = 'Delete old sqlite file, migrate new models, and load fake data'

    option_list = BaseCommand.option_list + (
            make_option('-P','--add-participants',type=int,dest='participants',
                default=0,help='Number of participants to add. Default = 0'),
            make_option('-J','--jennifer',default=False,action='store_true',
                help='Add a fake account for Jennifer to each facility'),
            make_option('-F','--facility',default=None,help='Force participants into one facility'),
        )

    def handle(self,*args,**options):

        #Delete old DB
        print 'Deleting old sqlite db....'
        try:
            if settings.ON_OPENSHIFT:
                os.remove(os.path.join(os.environ['OPENSHIFT_DATA_DIR'],'mwach.db'))
            else:
                os.remove(os.path.join(settings.PROJECT_PATH,'mwach.db'))
        except OSError:
            pass

        if not os.path.isfile(JSON_DATA_FILE):
            sys.exit('JSON file %s Does Not Exist'%(JSON_DATA_FILE,))

        #Migrate new models
        print 'Migrating new db....'
        utility = ManagementUtility(['reset_db.py','migrate'])
        utility.execute()

        #Turn off Autocommit
        #transaction.set_autocommit(False)

        config.CURRENT_DATE = datetime.date.today()
        with transaction.atomic():
            #Add new fake data
            create_facilities()
            create_users()

            if options['participants'] > 0:
                load_old_participants(options)

            if options['jennifer']:
                add_jennifers()

        #commit data
        #transaction.commit()

###################
# Utility Functions
###################

study_groups = ['control','one-way','two-way']
def add_client(client,study_id,facility=None):
    if facility:
        facility_list = cont.Facility.objects.filter(name=facility)
    else:
        facility_list = cont.Facility.objects.all()
    mod = len(facility_list)
    new_client = {
        'study_id':study_id,
        'anc_num':client['anc_num'],
        'nickname':client['nickname'],
        'birthdate':client['birth_date'],
        'study_group':random.choice(study_groups),
        'due_date':get_due_date(),
        'last_msg_client':client['last_msg_client'],
        'facility':facility_list[study_id%mod],
        'status':'post' if random.random() < .25 else 'pregnant',
        }
    contact = cont.Contact.objects.create(**new_client)
    connection = cont.Connection.objects.create(identity='+2500'+client['phone_number'][:8],contact=contact,is_primary=True)

    message_count = len(client['messages'])
    for i,m in enumerate(client['messages']):
        #only make translations for last five messages
        translate = i < message_count - 5
        add_message(m,contact,connection,translate)
    for v in client['visits']:
        add_visit(v,contact)
    for n in client['notes']:
        add_note(n,contact)
    add_new_visit(contact,study_id)
    add_new_calls(contact)
    add_new_scheduled_call(contact,study_id)

    return new_client

def add_message(message,contact,connection,translate=False):
    outgoing = message['sent_by'] != 'Client'
    system = message['sent_by'] == 'System'

    new_message = {
        'text':message['content'],
        'is_outgoing':outgoing,
        'is_system':system,
        'contact':contact,
        'connection':connection,
        'created':message['date'],
    }
    _message = cont.Message.objects.create(**new_message)

    if translate and not system:
        _message.translated_text = "(translated)" + message['content']
        _message.translation_status = 'done'
        _message.lanagues = random.choice(('english','swahili','sheng','luo'))

    _message.save()

def add_visit(visit,contact):
    if visit['scheduled_date']:
        new_visit = {
            'scheduled':visit['scheduled_date'],
            'notification_last_seen':dateutil.parser.parse(visit['scheduled_date'])-datetime.timedelta(days=1),
            'arrived':visit['date'],
            'skipped':True if random.random() < .25 else False,
            'comment':visit['comments'],
            'participant':contact
        }
        cont.Visit.objects.create(**new_visit)

VISIT_COUNT = 0
def add_new_visit(contact,i):
    new_visit = {
        'scheduled':utils.today() + datetime.timedelta(days=i+1),
        'participant':contact,
    }
    cont.Visit.objects.create(**new_visit)

def add_new_calls(contact):

    contact.add_call( outcome=random.choice(cont.PhoneCall.OUTCOME_CHOICES)[0],
        comment = 'This is a phone call that came in. Do we need a field for length')

    contact.add_call(outcome=random.choice(cont.PhoneCall.OUTCOME_CHOICES)[0],
        comment = 'This is an outgoing phone call. It was probably made at 1 month')

def add_new_scheduled_call(contact,i):

    scheduled_date = utils.today() + datetime.timedelta(days=2*i+1)
    cont.ScheduledPhoneCall.objects.create(scheduled=scheduled_date,participant=contact)
    cont.ScheduledPhoneCall.objects.create(
        scheduled=scheduled_date+datetime.timedelta(days=1),
        participant=contact,
        call_type='y')

def add_note(note,contact):
    new_note = {
        'contact':contact,
        'comment':note['content'],
        'created':note['date'],
    }

    _note = cont.Note.objects.create(**new_note)
    _note.save()


def get_due_date():
    return datetime.date.today() + datetime.timedelta(days=random.randint(0,100))

def load_old_participants(options):
        n = options['participants']
        print 'Loading %i Participants'%n
        clients = json.load(open(JSON_DATA_FILE))
        IMPORT_COUNT = min(n,len(clients))
        clients = clients.values()[:IMPORT_COUNT]

        for i,c in enumerate(clients):
            print add_client(c,i,options['facility'])

        #Mark the last message for each contact is_viewed=False
        last_messages = cont.Message.objects.filter(is_outgoing=False).values('contact_id').order_by().annotate(Max('id'))
        cont.Message.objects.exclude(id__in=[d['id__max'] for d in last_messages]).update(is_viewed=True)
        #Move the last message to the front of the message que
        for msg in cont.Message.objects.filter(id__in=[d['id__max'] for d in last_messages]):
            before_msg = msg.contact.message_set.all()[random.randint(1,3)]
            msg.created = before_msg.created + datetime.timedelta(seconds=600)
            msg.save()

        # Make last visit arrived = None.
        last_visits = cont.Visit.objects.all().values('participant_id').order_by().annotate(Max('id'))
        cont.Visit.objects.filter(id__in=[d['id__max'] for d in last_visits]).update(arrived=None,skipped=None)

def add_jennifers():
    print 'Loading Fake Jennifer Users'
    for i,facility in enumerate(cont.Facility.objects.all()):
        create_jennifer(i,facility)

def create_jennifer(i,facility):
    new_client = {
        'study_id':1000+i,
        'anc_num':'100{}'.format(i),
        'nickname':'Jennifer',
        'birthdate':'1900-01-01',
        'study_group':random.choice(study_groups),
        'due_date':get_due_date(),
        'facility':facility,
        'status':'pregnant',
        }
    contact = cont.Contact.objects.create(**new_client)
    connection = cont.Connection.objects.create(identity='+00{}'.format(i),contact=contact,is_primary=True)


def create_facilities():
    print 'Creating Facilities'
    cont.Facility.objects.bulk_create([
        cont.Facility(name='bondo'),
        cont.Facility(name='ahero'),
        cont.Facility(name='mathare'),
    ])

def create_users():
    #create admin user
    print 'Creating Users'
    oscard = User.objects.create_superuser('admin',email='o@o.org',password='mwachx')
    cont.Practitioner.objects.create(facility=cont.Facility.objects.get(pk=1),user=oscard)
    #create study nurse users
    facility_list = ['bondo','ahero','mathare']
    for f in facility_list:
        user = User.objects.create_user('n_{}'.format(f),password='mwachx')
        cont.Practitioner.objects.create(facility=cont.Facility.objects.get(name=f),user=user)
