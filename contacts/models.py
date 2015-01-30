from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

#Local Imports
from utils.models import TimeStampedModel

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
    )
    
    CONDITION_CHOICES = (
        ('normal','Normal'),
        ('adolescent','Adolescent'),
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
    due_date = models.DateField(verbose_name='Due Date')
    
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
        return Connection.objects.get(contact=self,is_primary=True)
        
    @property
    def phone_number(self):
        return self.connection.identity
    
class PhoneCall(TimeStampedModel):
        
    contact = models.ForeignKey(settings.MESSAGING_CONTACT)
    answered = models.BooleanField(default=False)
    incomming = models.BooleanField(default=True)
    comment = models.CharField(max_length=500,blank=True,null=True)
    
class Note(TimeStampedModel):
        
    contact = models.ForeignKey(settings.MESSAGING_CONTACT)
    admin = models.ForeignKey(settings.MESSAGING_ADMIN, blank=True, null=True)
    comment = models.CharField(max_length=500,blank=True,null=True)
    
class Visit(TimeStampedModel):
    class Meta:
        ordering = ('scheduled',)
    
    contact = models.ForeignKey(settings.MESSAGING_CONTACT)
    scheduled = models.DateField(blank=True,null=True)
    arrived = models.DateField(blank=True,null=True)
    skipped = models.BooleanField(default=False)
    comment = models.CharField(max_length=500,blank=True,null=True)
    
    def study_id(self):
        return self.contact.id
    study_id.short_description = 'Study ID'
    study_id.admin_order_field = 'contact__study_id'
    
    def contact_name(self):
        return self.contact.nickname
    contact_name.short_description = 'Nickname'
    contact_name.admin_order_field = 'contact__nickname'
    
    
class StatusChange(TimeStampedModel):
    class Meta:
        ordering = ('created',)
    
    contact = models.ForeignKey(settings.MESSAGING_CONTACT)
    old = models.CharField(max_length=20,choices=Contact.STATUS_CHOICES)
    new = models.CharField(max_length=20,choices=Contact.STATUS_CHOICES)

class Connection(TimeStampedModel):
    
    TYPE_CHOICES = (
        ('phone','Phone Number'),
        ('email','Email'),
    )
    
    identity = models.CharField(max_length=25,primary_key=True)
    contact = models.ForeignKey(settings.MESSAGING_CONTACT,blank=True,null=True)
    
    description = models.CharField(max_length=150,blank=True,null=True,help_text='Description of phone numbers relationship to contact')
    connection_type = models.CharField(max_length=10,help_text='Type of connection',default='phone')
    
    is_primary = models.BooleanField(default=False)
    
class Message(TimeStampedModel):
    
    class Meta:
        ordering = ('-created',)
    
    text = models.CharField(max_length=1000,help_text='Text of the SMS message')
    
    #Boolean Flags on Message
    is_outgoing = models.BooleanField(default=True)
    is_system = models.BooleanField(default=True)
    is_viewed = models.BooleanField(default=False)
    
    # ToDo:Link To Automated Message
    reply = models.ForeignKey('contacts.Message',related_name='parent',blank=True,null=True)

    admin_user = models.ForeignKey(settings.MESSAGING_ADMIN, blank=True, null=True)
    connection = models.ForeignKey(settings.MESSAGING_CONNECTION)
    contact = models.ForeignKey(settings.MESSAGING_CONTACT,blank=True,null=True)
    
    def html_class(self):
        '''
        Determines how to display the message in a template
        '''
        if self.is_outgoing:
            return 'system' if self.is_system else 'nurse'
        return 'client'
    
    def sent_by(self):
        if self.is_outgoing:
            if self.is_system:
                return 'System'
            return self.admin_user.username if self.admin_user else 'Nurse'
        return self.contact_name()
    
    def study_id(self):
        if self.contact:
            return self.contact.study_id
        return None
    study_id.short_description = 'Study ID'
    study_id.admin_order_field = 'contact__study_id'
    
    def contact_name(self):
        if self.contact:
            return str(self.contact.nickname)
        return None
    contact_name.short_description = 'Contact Name'
    contact_name.admin_order_field = 'contact__nickname'
    
    def identity(self):
        return self.connection.identity
    identity.short_description = 'Identity'
    identity.admin_order_field = 'connection__identity'
    
    @staticmethod
    def receive(number,message):
        '''
        Main hook for receiving messages
            * number: the phone number of the incoming message
            * message: the text of the incoming message
        '''
        #Get incoming connection
        connection,created = Connection.get_or_create(identity=number)
        Message.objects.create(
            is_system=False,
            is_outgoing=False,
            text=message,
            connection=connection,
            contact=connection.contact
        )
        
    @staticmethod
    def send(contact,message,is_system=True):
        Message.objects.create(
            is_system=is_system,
            text=message,
            connection=contact.connection,
            contact=contact,
            is_viewed=True,
        )



