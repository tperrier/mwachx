#!/usr/bin/python
#Python Imports
from hashlib import sha256
import math

#Django Imports
from django.conf import settings
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

#Local Imports
from utils.models import TimeStampedModel, BaseQuerySet, ForUserQuerySet
from contacts.models import Message, PhoneCall, Practitioner
import backend.models as back
import utils
import transports

class ContactQuerySet(ForUserQuerySet):

    participant_field = None

    def pregnant(self):
        return self.filter(models.Q(status='pregnant')|models.Q(status='over'))

    def active(self):
        return self.exclude(models.Q(status='completed')|models.Q(status='stopped')|models.Q('other'))

    def post_partum(self):
        return self.filter(models.Q(status='post')|models.Q(status='ccc'))

    def has_pending(self):
        return set([message.contact for message in Message.objects.pending().prefetch_related('contact')])



class Contact(TimeStampedModel):

    STATUS_CHOICES = (
        ('pregnant','Pregnant'),
        ('over','Post-Date'),
        ('post','Post-Partum'),
        ('ccc','CCC'),
        ('completed','Completed'),
        ('stopped','Withdrew'),
        ('other','Stopped Other')
    )

    GROUP_CHOICES = (
        ('control','Control'),
        ('one-way','One Way'),
        ('two-way','Two Way'),
    )

    LANGUAGE_CHOICES = (
        ('english','English'),
        ('luo','Luo'),
        ('swahili','Swahili'),
    )

    CONDITION_CHOICES = (
        ('art','1 - Starting ART'),
        ('adolescent','2 - Adolescent'),
        ('first','3 - First Time Mother'),
        ('normal','4 -  Normal'),
    )

    FAMILY_PLANNING_CHOICES = (
        ('none','None'),
        ('iud','IUD'),
        ('pill','Pills'),
        ('depot','Depot'),
        ('implant','Implant'),

    )

    RELATIONSHIP_CHOICES = (
        ('single','Single'),
        ('partner','Partner'),
        ('married','Married'),
        ('seperated','Seperated'),
    )

    DAY_CHOICES = (
        (0,'Monday'),
        (1,'Tuesday'),
        (2,'Wednesday'),
        (3,'Thursday'),
        (4,'Friday'),
        (5,'Satuday'),
        (6,'Sunday'),
    )

    TIME_CHOICES = (
        (8,'Morning (8 AM)'),
        (13,'Afternoon (1 PM)'),
        (20,'Evening (8 PM)'),
    )

    MESSAGING_CHOICES = (
        ('none','No HIV Messaging'),
        ('initiated','HIV Content If Initiated'),
        ('system','HIV Content Allowed'),
    )

    DELIVERY_SOURCE_CHOICES = (
        ('phone','Phone'),
        ('sms','SMS'),
        ('visit','Clinic Visit'),
        ('other','Other'),
    )

    #Set Custom Manager
    objects = ContactQuerySet.as_manager()

    #Study Attributes
    study_id = models.CharField(max_length=10,unique=True,verbose_name='Study ID',help_text="* Use Barcode Scanner")
    anc_num = models.CharField(max_length=15,verbose_name='ANC #')
    ccc_num = models.CharField(max_length=15,verbose_name='CCC #',blank=True,null=True)
    facility = models.CharField(max_length=15,choices=settings.FACILITY_CHOICES)

    study_group = models.CharField(max_length=10,choices=GROUP_CHOICES,verbose_name='Group')
    send_day = models.IntegerField(choices=DAY_CHOICES, default=0,verbose_name='Send Day')
    send_time = models.IntegerField(choices=TIME_CHOICES,default=8,verbose_name='Send Time')

    # Required Client Personal Information
    nickname = models.CharField(max_length=20)
    birthdate = models.DateField(verbose_name='DOB')

    # Optional Clinet Personal Informaiton
    partner_name = models.CharField(max_length=40,blank=True,verbose_name='Partner Name')
    relationship_status = models.CharField(max_length=15,choices=RELATIONSHIP_CHOICES,verbose_name='Relationship Status',blank=True)
    previous_pregnancies = models.IntegerField(blank=True,null=True,help_text='* excluding current')
    phone_shared = models.NullBooleanField(verbose_name='Phone Shared')

    # Required Medical Information
    status = models.CharField(max_length=15,choices=STATUS_CHOICES, default='pregnant')
    language = models.CharField(max_length=10,choices=LANGUAGE_CHOICES,default='english')
    condition = models.CharField(max_length=15,choices=CONDITION_CHOICES,default='normal')
    due_date = models.DateField(verbose_name='Estimated Delivery Date')

    delivery_date = models.DateField(verbose_name='Delivery Date',blank=True,null=True)
    delivery_source = models.CharField(max_length=10,verbose_name="Delivery Notification Source",choices=DELIVERY_SOURCE_CHOICES,blank=True)

    # Optional Medical Informaton
    art_initiation = models.DateField(blank=True,null=True,help_text='Date of ART Initiation',verbose_name='ART Initiation')
    hiv_disclosed = models.NullBooleanField(blank=True,verbose_name='HIV Disclosed')
    hiv_messaging = models.CharField(max_length=15,choices=MESSAGING_CHOICES,default='none',verbose_name='HIV Messaging')
    child_hiv_status = models.NullBooleanField(blank=True,verbose_name='Child HIV Status')
    family_planning = models.CharField(max_length=10,blank=True,choices=FAMILY_PLANNING_CHOICES,verbose_name='Family Planning')

    #State attributes to be edited by the system
    last_msg_client = models.DateField(blank=True,null=True,help_text='Date of last client message received',editable=False)
    last_msg_system = models.DateField(blank=True,null=True,help_text='Date of last system message sent',editable=False)
    is_validated = models.BooleanField(default=False,blank=True)
    validation_key = models.CharField(max_length=5,blank=True)

    class Meta:
        app_label = 'contacts'
    participant_field = None

    def __init__(self, *args, **kwargs):
        ''' Override __init__ to save old status'''
        super(Contact,self).__init__(*args,**kwargs)
        self._old_status = self.status
        self._old_hiv_messaging = self.hiv_messaging

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        # Check that self.id exists so this is not the first save
        if not self._old_status == self.status and self.id is not None:
            self.statuschange_set.create(old=self._old_status,new=self.status,comment='Status Admin Change')

        if not self._old_hiv_messaging == self.hiv_messaging and self.id is not None:
            print self._old_hiv_messaging, self.hiv_messaging
            self.statuschange_set.create(old=self._old_hiv_messaging,new=self.hiv_messaging,
                comment='HIV messaging changed',type='hiv')

        # Forc capitalization of nickname
        self.nickname = self.nickname.capitalize()

        super(Contact,self).save(force_insert,force_update,*args,**kwargs)
        self._old_status = self.status

    def __str__ (self):
        return self.nickname

    def __repr__(self):
        return "(#%03s) %s - %s"%(self.study_id,self.nickname,self.facility)

    def connection(self):
        return self.connection_set.filter(is_primary=True).first()
        # from contacts.models import Connection
        # return Connection.objects.filter(contact=self,is_primary=True).first()

    def phone_number(self):
        return self.connection().identity

    def is_active(self):
        return not (self.status == 'completed' or self.status == 'stopped' or self.status == 'other')

    def age(self):
        today = utils.today()
        delta = today - self.birthdate
        return int((delta.days - delta.seconds/86400.0)/365.2425)

    def get_scheduled_visits(self):
        ''' Return all currently scheduled visits '''
        return self.visit_set.filter(skipped__isnull=True)

    def get_pending_messages(self):
        ''' Return all currently pending messages '''
        return self.message_set.pending()

    def is_pregnant(self):
        return self.status == 'pregnant' or self.status == 'over'

    def was_pregnant(self,today=None):
        '''
        Returns true if the contact was pregnant at date today
        '''
        if self.delivery_date is not None:
            today = utils.today(today)
            return today <= self.delivery_date
        return True

    def delta_days(self,today=None):
        '''
        Return the number days until EDD or since delivery
        '''
        today = utils.today(today)
        if self.was_pregnant(today):
            # Return 40*7 - days until due date
            return 280 - (self.due_date - today).days
        else: #post-partum
            #TODO: Change this to delivered date when we start using that
            # Return days since due date
            return (today-self.due_date).days

    def description(self,today=None,**kwargs):
        hiv_messaging = kwargs.get("hiv_messaging", self.hiv_messaging == "system")
        hiv = "Y" if hiv_messaging else "N"
        group = kwargs.get("group",self.study_group)

        send_base = kwargs.get("send_base",'edd' if self.was_pregnant(today) else 'dd')
        send_offset = kwargs.get("send_offset",self.delta_days(today=today)/7)

        return "{send_base}.{group}.{condition}.{hiv}.{send_offset}".format(
            group=group, condition=self.condition, hiv=hiv,
            send_base=send_base , send_offset=send_offset
        )

    def days_str(self,today=None):
        return utils.days_as_str(self.delta_days(today))

    def get_validation_key(self):
        sha = sha256('%s%s%s%s'%(self.study_id,self.nickname,self.anc_num,self.birthdate)).hexdigest()[:5]
        key = ''.join([str(int(i,16)) for i in sha])
        return key[:5]

    def choice_label(self):
        return '%s (%s)'%(self.nickname,self.facility)

    def add_call(self,outcome='answered',comment=None,length=None,is_outgoing=True,
                 created=None,admin_user=None,scheduled=None):
        if created is None:
            created = utils.today()
        else:
            created = utils.angular_datepicker(created)

        new_call = PhoneCall.objects.create(outcome=outcome,contact=self,is_outgoing=is_outgoing,
                        comment=comment,created=created,connection=self.connection(),length=length,
                        scheduled=scheduled)
        return new_call

    def delivery(self, delivery_date, comment='', user=None, source=None):

        self.delivery_date = delivery_date
        self.delivery_source = source
        self.set_status('post',comment='Post-partum set by {0}'.format(user))
        self.note_set.create(comment=comment,admin=user)

    def set_status(self, new_status, comment=''):
        old_status = self.status
        self.status = new_status
        self._old_status = new_status # Disable auto status change message
        self.save()

        self.statuschange_set.create(
            old = old_status, new = new_status, comment = comment
        )

    def message_kwargs(self):
        return {
            'name':self.nickname.title(),
            'nurse':Practitioner.objects.filter(facility=self.facility)
                .exclude(user__first_name='').first().user.first_name,
            'clinic':self.facility.title()
        }

    def send_message(self,text,control=False,**kwargs):

        if self.study_group != 'control' or control:
            # Make sure we don't send messages to the control group
            # Send message over system transport
            try:
                msg_id, msg_success, external_data = transports.send(self.phone_number(),text)
            except transports.TransportError as e:
                msg_id = ''
                msg_success = False
                external_data = {'error':str(e)}
        else:
            text = 'CONTROL NOT SENT: ' + text
            msg_id = 'control'
            msg_success = False
            external_data = {}

        # Create new message
        new_message = self.message_set.create(
            text=text,
            connection=self.connection(),
            external_id=msg_id,
            external_success=msg_success,
            external_data=external_data,
            **kwargs)

        return new_message

    def send_automated_message(self,control=False,send=True,**kwargs):
        message = back.AutomatedMessage.objects.for_participant(self,**kwargs)
        if message is None:
            return None #TODO: logging on this

        text = message.text_for(self)
        if text is None:
            return None #TODO: logging on this

        if send:
            return self.send_message(
                text=text,
                translation_status='auto',
                auto=message.description(),
                control=control
            )
        else:
            return message

class StatusChange(TimeStampedModel):

    objects = BaseQuerySet.as_manager()

    class Meta:
        app_label = 'contacts'

    contact = models.ForeignKey(settings.MESSAGING_CONTACT)

    old = models.CharField(max_length=20)
    new = models.CharField(max_length=20)
    type = models.CharField(max_length=10,default='status')

    comment = models.TextField(blank=True)

    def contact_name(self):
        if self.contact:
            return '<a href="../contact/{0.study_id}">{0.nickname}</a>'.format(self.contact)
        return None
    contact_name.short_description = 'Contact Name'
    contact_name.admin_order_field = 'contact__nickname'
    contact_name.allow_tags = True
