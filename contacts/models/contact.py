#!/usr/bin/python
#Python Imports
from hashlib import sha256
import math

#Django Imports
from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

#Local Imports
from utils.models import TimeStampedModel, BaseQuerySet
from contacts.models import Message
import utils

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
        ('dholuo','Dholuo'),
        ('kiswahili','KiSwahili'),
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
    )

    TIME_CHOICES = (
        (8,'Morning (8 AM)'),
        (13,'Afternoon (1 PM)'),
        (19,'Evening (7 PM)'),
    )

    CHILD_STATUS_CHOICES = (
        ('unknown','Unknown'),
        ('negative','Negative'),
        ('positive','Positive'),
    )

    #Set Custom Manager
    objects = ContactQuerySet.as_manager()

    #Study Attributes
    # NOTE: Updated to integer fields so that the validation can be done client side.
    study_id = models.IntegerField(unique=True,verbose_name='Study ID')
    anc_num = models.IntegerField(verbose_name='ANC #')

    facility = models.ForeignKey('contacts.Facility')

    study_group = models.CharField(max_length=10,choices=GROUP_CHOICES,verbose_name='Group')
    send_day = models.IntegerField(choices=DAY_CHOICES, default=3,verbose_name='Send Day')
    send_time = models.IntegerField(choices=TIME_CHOICES,default=13,verbose_name='Send Time')

    #Client Personal Information
    nickname = models.CharField(max_length=50)
    birthdate = models.DateField(verbose_name='DOB')
    partner_name = models.CharField(max_length=100,blank=True,null=True,verbose_name='Partner Name')
    relationship_status = models.CharField(max_length=30,choices=RELATIONSHIP_CHOICES,default='married',verbose_name='Relationship Status',blank=True,null=True)
    previous_pregnancies = models.IntegerField(default=0,blank=True,null=True)
    phone_shared = models.NullBooleanField(default=None,verbose_name='Phone Shared')

    #Medical Information
    status = models.CharField(max_length=20,choices=STATUS_CHOICES, default='pregnant')
    language = models.CharField(max_length=25,choices=LANGUAGE_CHOICES,default='english')
    condition = models.CharField(max_length=40,choices=CONDITION_CHOICES,default='normal')
    family_planning = models.CharField(max_length=50,blank=True,null=True,choices=FAMILY_PLANNING_CHOICES,default='none',verbose_name='Family Planning')
    art_initiation = models.DateField(blank=True,null=True,help_text='Date of ART Initiation',verbose_name='ART Initiation')
    hiv_disclosed = models.NullBooleanField(default=None,verbose_name='HIV Disclosed')
    child_hiv_status = models.CharField(max_length=20,choices=CHILD_STATUS_CHOICES,default='unknown',verbose_name='Child HIV Status')
    due_date = models.DateField(verbose_name='Estimated Delivery Date')
    delivery_date = models.DateField(verbose_name='Delivery Date',blank=True,null=True)

    #State attributes to be edited by the system
    last_msg_client = models.DateField(blank=True,null=True,help_text='Date of last client message received')
    last_msg_system = models.DateField(blank=True,null=True,help_text='Date of last system message sent')
    is_validated = models.BooleanField(default=False)

    class Meta:
        app_label = 'contacts'

    def __str__ (self):
        return self.nickname

    def __repr__(self):
        return "(#%03s) %s"%(self.study_id,self.nickname)

    @property
    def connection(self):
        from contacts.models import Connection
        return Connection.objects.filter(contact=self,is_primary=True).first()

    @property
    def phone_number(self):
        return self.connection.identity

    @property
    def is_pregnant(self):
        return self.status == 'pregnant' or self.status == 'over'

    def was_pregnant(self,today=None):
        '''
        Returns true if the contact was pregnant at date today
        '''
        #ToDo: we need to add a delivery_date field to contact and use that here
        if today is None:
            today = settings.utils.today()
        return today < self.due_date

    @property
    def is_active(self):
        return not (self.status == 'completed' or self.status == 'stopped' or self.status == 'other')

    @property
    def age(self):
        today = utils.today()
        delta = today - self.birthdate
        return int((delta.days - delta.seconds/86400.0)/365.2425)

    @property
    def get_visits(self):
        return self.visit_set.filter(~models.Q(skipped=False))

    def weeks(self,today=None):
        '''
        Returns the number weeks until EDD or since delivery
        '''
        if today is None:
            today = utils.today()
        if self.was_pregnant(today):
            days = (self.due_date - today).days
            weeks =  days/7
            return 40 - weeks
        else: #post-partum
            return (today-self.due_date).days/7 #ToDO: Change this to delivered date when we start using that

    def weeks_display(self):
        return 'EGA: %i wks'%self.weeks()

    def study_id_short(self):
        return '%04i'%self.study_id

    def validation_key(self):
        sha = sha256('%i%s%i%s'%(self.id,self.nickname,self.anc_num,self.birthdate)).hexdigest()[:5]
        key = ''.join([str(int(i,16)) for i in sha])
        return key[:5]

    def choice_label(self):
        return '%s (%s)'%(self.nickname,self.facility)

    def send_message(self,text,**kwargs):
        new_message = Message.objects.create(text=text,contact=self,connection=self.connection,**kwargs)
        return new_message

    @property
    def pending(self):
        return Message.objects.filter(contact=self,is_viewed=False).count()
