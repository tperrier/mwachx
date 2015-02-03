#!/usr/bin/python
#Django Imports
from django.db import models
from django.conf import settings

#Local Imports
from utils.models import TimeStampedModel, BaseQuerySet
from contacts.models import Message

class ContactQuerySet(BaseQuerySet):
    
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
        ('normal','Normal'),
        ('adolescent','Adolescent'),
        ('first','First Time Mother'),
        ('cesarean','Previous Cesarean'),
        ('art','Starting Art'),
    )
    
    FAMILY_PLANNING_CHOICES = (
        ('none','None'),
        ('iud','IUD'),
        ('pill','Pills'),
    )
    
    RELATIONSHIP_CHOICES = (
        ('single','Single'),
        ('parner','Parner'),
        ('married','Married'),
    )
    
    DAY_CHOICES = (
        (0,'Monday'),
        (1,'Tuesday'),
        (2,'Wednesday'),
        (3,'Thursday'),
        (4,'Friday'),
        (5,'Saturday'),
        (6,'Sunday'),
    )
    
    TIME_CHOICES = (
        (8,'Morning'),
        (13,'Afternoon'),
        (19,'Evening'),
    )
    
    CHILD_STATUS_CHOICES = (
        ('unknown','Unkown'),
        ('negative','Negative'),
        ('positive','Positive'),
    )
    
    #Set Custom Manager
    objects = ContactQuerySet.as_manager()
    
    #Study Attributes
    study_id = models.PositiveIntegerField(unique=True,verbose_name='Study ID')
    anc_num = models.PositiveIntegerField(verbose_name='ANC #')
    
    study_group = models.CharField(max_length=10,choices=GROUP_CHOICES,verbose_name='Group')
    send_day = models.IntegerField(choices=DAY_CHOICES, default=3,verbose_name='Send Day')
    send_time = models.IntegerField(choices=TIME_CHOICES,default=13,verbose_name='Send Time')

    #Client Personal Information
    nickname = models.CharField(max_length=50)
    birthdate = models.DateField(verbose_name='DOB')
    partner_name = models.CharField(max_length=100,blank=True,null=True,verbose_name='Partner Name')
    relationship_status = models.CharField(max_length=30,choices=RELATIONSHIP_CHOICES,default='married',verbose_name='Relationship Status')
    previous_pregnancies = models.IntegerField(default=0)
    
    #Medical Information
    status = models.CharField(max_length=20,choices=STATUS_CHOICES, default='pregnant')
    language = models.CharField(max_length=25,choices=LANGUAGE_CHOICES,default='english')
    condition = models.CharField(max_length=40,choices=CONDITION_CHOICES,default='normal')
    family_planning = models.CharField(max_length=50,blank=True,null=True,choices=FAMILY_PLANNING_CHOICES,default='none')
    art_initiation = models.DateField(blank=True,null=True,help_text='Date of ART initiation',verbose_name='ART Initiantion')
    hiv_disclosed = models.NullBooleanField(default=None)
    child_hiv_status = models.CharField(max_length=20,choices=CHILD_STATUS_CHOICES,default='unkown')
    due_date = models.DateField(verbose_name='Expected Delivery')
    
    #State attributes to be edited by the system
    last_msg_client = models.DateField(blank=True,null=True,help_text='Date of last client message received')
    last_msg_system = models.DateField(blank=True,null=True,help_text='Date of last system message sent')
    is_validated = models.BooleanField(default=False)
    
    def __str__ (self):
        return self.nickname
        
    def __repr__(self):
        return "(#%03s) %s"%(self.study_id,self.nickname)
        
    @property
    def connection(self):
        from contacts.models import Connection
        return Connection.objects.get(contact=self,is_primary=True)
        
    @property
    def phone_number(self):
        return self.connection.identity
        
    @property 
    def is_pregnant(self):
        return self.status == 'pregnant' or self.status == 'over'
        
    @property
    def is_active(self):
        return not (self.status == 'completed' or self.status == 'stopped' or self.status == 'other')
    
    @property
    def age(self):
        today = settings.CURRENT_DATE
        delta = today - self.birthdate
        return int((delta.days - delta.seconds/86400.0)/365.2425)
        
    def weeks(self,today=None):
        '''
        Returns the number weeks until EDD or since delivery
        '''
        if today is None:
            today = settings.CURRENT_DATE
        if self.is_pregnant:
            days = (self.due_date - today).days
            weeks =  days/7
            return 40 - weeks
        
    def weeks_display(self):
        return 'EGA: %i wks'%self.weeks()
        
    def study_id_short(self):
        return '%04i'%self.study_id
    
    @property
    def pending(self):
        return Message.objects.filter(contact=self,is_viewed=False).count()

