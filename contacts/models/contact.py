#!/usr/bin/python
#Python Imports
from hashlib import sha256
import math

#Django Imports
from django.conf import settings
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

#Local Imports
from utils.models import TimeStampedModel, BaseQuerySet
from contacts.models import Message, PhoneCall
import backend.models as back
import utils
import transports

class ContactQuerySet(BaseQuerySet):

    def for_user(self,user):
        try:
            return self.filter(facility=user.practitioner.facility)
        except ObjectDoesNotExist:
            return self.none()


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
        ('art','Starting ART'),
        ('adolescent','Adolescent'),
        ('first','First Time Mother'),
        ('normal','Normal'),
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
        ('','No HIV Messaging'),
        ('initiated','HIV Content If Initiated'),
        ('system','HIV Content Allowed'),
    )

    #Set Custom Manager
    objects = ContactQuerySet.as_manager()

    #Study Attributes
    study_id = models.CharField(max_length=10,unique=True,verbose_name='Study ID',help_text="* Use Barcode Scanner")
    anc_num = models.CharField(max_length=15,verbose_name='ANC #')
    ccc_num = models.CharField(max_length=15,verbose_name='CCC #',blank=True,null=True)
    facility = models.ForeignKey('backend.Facility')

    study_group = models.CharField(max_length=10,choices=GROUP_CHOICES,verbose_name='Group')
    send_day = models.IntegerField(choices=DAY_CHOICES, default=0,verbose_name='Send Day')
    send_time = models.IntegerField(choices=TIME_CHOICES,default=8,verbose_name='Send Time')

    # Required Client Personal Information
    nickname = models.CharField(max_length=20)
    birthdate = models.DateField(verbose_name='DOB')

    # Optional Clinet Personal Informaiton
    partner_name = models.CharField(max_length=40,blank=True,verbose_name='Partner Name')
    relationship_status = models.CharField(max_length=15,choices=RELATIONSHIP_CHOICES,verbose_name='Relationship Status',blank=True)
    previous_pregnancies = models.IntegerField(blank=True,null=True)
    phone_shared = models.NullBooleanField(verbose_name='Phone Shared')

    # Required Medical Information
    status = models.CharField(max_length=15,choices=STATUS_CHOICES, default='pregnant')
    language = models.CharField(max_length=10,choices=LANGUAGE_CHOICES,default='english')
    condition = models.CharField(max_length=15,choices=CONDITION_CHOICES,default='normal')
    due_date = models.DateField(verbose_name='Estimated Delivery Date')

    delivery_date = models.DateField(verbose_name='Delivery Date',blank=True,null=True)

    # Optional Medical Informaton
    art_initiation = models.DateField(blank=True,null=True,help_text='Date of ART Initiation',verbose_name='ART Initiation')
    hiv_disclosed = models.NullBooleanField(blank=True,verbose_name='HIV Disclosed')
    hiv_messaging = models.CharField(max_length=15,default='',blank=True,choices=MESSAGING_CHOICES,verbose_name='HIV Messaging')
    child_hiv_status = models.NullBooleanField(blank=True,verbose_name='Child HIV Status')
    family_planning = models.CharField(max_length=10,blank=True,choices=FAMILY_PLANNING_CHOICES,verbose_name='Family Planning')

    #State attributes to be edited by the system
    last_msg_client = models.DateField(blank=True,null=True,help_text='Date of last client message received',editable=False)
    last_msg_system = models.DateField(blank=True,null=True,help_text='Date of last system message sent',editable=False)
    is_validated = models.BooleanField(default=False,blank=True)
    validation_key = models.CharField(max_length=5,blank=True)

    class Meta:
        app_label = 'contacts'

    def __str__ (self):
        return self.nickname

    def __repr__(self):
        return "(#%03s) %s - %s"%(self.study_id,self.nickname,self.facility)

    # @property
    def connection(self):
        return self.connection_set.filter(is_primary=True).first()
        # from contacts.models import Connection
        # return Connection.objects.filter(contact=self,is_primary=True).first()

    # @property
    def phone_number(self):
        return self.connection().identity

    # @property
    def is_active(self):
        return not (self.status == 'completed' or self.status == 'stopped' or self.status == 'other')

    # @property
    def age(self):
        today = utils.today()
        delta = today - self.birthdate
        return int((delta.days - delta.seconds/86400.0)/365.2425)

    ''' ~REMOVE
    @property
    def get_visits(self):
        return self.visit_set.filter(~models.Q(skipped=False))
    '''

    def get_scheduled_visits(self):
        ''' Return all currently scheduled visits '''
        return self.visit_set.filter(skipped__isnull=True)

    def get_pending_messages(self):
        ''' Return all currently pending messages '''
        return self.message_set.pending()

    # @property
    def is_pregnant(self):
        return self.status == 'pregnant' or self.status == 'over'

    def was_pregnant(self,today=None):
        '''
        Returns true if the contact was pregnant at date today
        '''
        #ToDo: we need to add a delivery_date field to contact and use that here
        if today is None:
            today = utils.today()
        return today < self.due_date

    def delta_days(self,today=None):
        '''
        Return the number days until EDD or since delivery
        '''
        if today is None:
            today = utils.today()

        if self.was_pregnant(today):
            # Return 40*7 - days until due date
            return 280 - (self.due_date - today).days
        else: #post-partum
            #ToDO: Change this to delivered date when we start using that
            # Return days since due date
            return (today-self.due_date).days

    def days_str(self,today=None):
        return utils.days_as_str(self.delta_days(today))

    ''' ~REMOVE
    def study_id_short(self):
        return '%04i'%self.study_id
    '''

    def get_validation_key(self):
        sha = sha256('%i%s%s%s'%(self.study_id,self.nickname,self.anc_num,self.birthdate)).hexdigest()[:5]
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

    def delivery(self, delivery_date, comment=None):

        self.delivery_date = delivery_date
        self.set_status('post', comment)

    def set_status(self, new_status, comment=None):
        old_status = self.status
        self.status = new_status
        self.save()

        self.statuschange_set.create(
            old = old_status, new = new_status, comment = comment
        )

    def send_message(self,text,**kwargs):

        if self.study_group != 'control': # Make sure we don't send messages to the control group
            # Send message over system transport
            try:
                msg_id = transports.send(self.phone_number(),text)
            except transports.TransportError as e:
                msg_id = 'error'
        else:
            text = 'WARNING: Message not sent control' + text
            msg_id = 'control'

        # Create new message
        new_message = self.message_set.create(
            text=text,
            connection=self.connection(),
            external_id=msg_id,
            **kwargs)

        return new_message

    def send_automated_message(self,send_base=None,send_offset=0):
        # potential_messages = back.AutomatedMessage.objects.filter(
        #     send_base__name=send_base,
        #     send_offset=send_offset
        # )
        # message = potential_messages.first()
        message = back.AutomatedMessage.objects.filter_participant(self,send_base,send_offset)
        self.send_message(text=message.for_participant(self),translation_status='auto',auto=message)


class StatusChange(TimeStampedModel):

    objects = BaseQuerySet.as_manager()

    class Meta:
        app_label = 'contacts'

    contact = models.ForeignKey(settings.MESSAGING_CONTACT)

    old = models.CharField(max_length=20,choices=Contact.STATUS_CHOICES)
    new = models.CharField(max_length=20,choices=Contact.STATUS_CHOICES)

    comment = models.TextField()

    def contact_name(self):
        if self.contact:
            return '<a href="../contact/{0.study_id}">{0.nickname}</a>'.format(self.contact)
        return None
    contact_name.short_description = 'Contact Name'
    contact_name.admin_order_field = 'contact__nickname'
    contact_name.allow_tags = True
