from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

#Local Imports
from utils.models import TimeStampedModel

class Contact(TimeStampedModel):
    
    STATUS_CHOICES = (
        ('Pregnant','Pregnant'),
        ('Over','Post-Date'),
        ('Post','Post-Partum'),
        ('CCC','CCC'),
        ('Completed','Completed'),
        ('Stopped','Withdrew'),
        ('Other','Stopped Other')
    )
    
    GROUP_CHOICES = (
        ('control','Control'),
        ('one-way','One Way'),
        ('two-way','Two Way'),
    )
    
    study_id = models.PositiveIntegerField(unique=True)
    anc_num = models.PositiveIntegerField()
    
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    nick_name = models.CharField(max_length=50)
    
    birth_date = models.DateField()
    
    status = models.CharField(max_length=20,choices=STATUS_CHOICES, default='Pregnant')
    due_date = models.DateField()
    
    study_group = models.CharField(max_length=10,choices=GROUP_CHOICES)
    
class Interaction(TimeStampedModel):
    
    class Meta:
        abstract = True
        ordering = ('-created',)
        
    user = models.ForeignKey(User)
    contact = models.ForeignKey(settings.MESSAGING_CONTACT)
    
    comment = models.CharField(max_length=500,blank=True,null=True)
    
class PhoneCall(Interaction):
    
    answered = models.BooleanField(default=False)
    incomming = models.BooleanField(default=True)
    
    reason = models.CharField(max_length=250,blank=True,null=True)
    
class Note(Interaction):
    pass
    
class Visit(Interaction):
    
    scheduled = models.DateField()
    attended = models.DateField(blank=True,null=True)
    
class StatusChange(Interaction):
    
    old = models.CharField(max_length=20,choices=Contact.STATUS_CHOICES)
    new = models.CharField(max_length=20,choices=Contact.STATUS_CHOICES)

class Connection(TimeStampedModel):
    identity = models.CharField(max_length=25,primary_key=True)
    contact = models.ForeignKey(settings.MESSAGING_CONTACT,blank=True,null=True)
    
class Message(TimeStampedModel):
    
    class Meta:
        ordering = ('-created',)
    
    text = models.CharField(max_length=1000)
    
    is_outgoing = models.BooleanField(default=True)
    is_system = models.BooleanField(default=True)
    user = models.ForeignKey(User,blank=True,null=True)

    connection = models.ForeignKey(settings.MESSAGING_CONNECTION)
    contact = models.ForeignKey(settings.MESSAGING_CONTACT,blank=True,null=True)
    
    def study_id(self):
        if self.contact:
            return self.contact.study_id
        return None
    study_id.short_description = 'Study ID'
    study_id.admin_order_field = 'contact__study_id'
    
    def first_name(self):
        if self.contact:
            return self.contact.first_name
        return None
    first_name.short_description = 'First Name'
    first_name.admin_order_field = 'contact__first_name'
    
    def last_name(self):
        if self.contact:
            return self.contact.last_name
        return None
    last_name.short_description = 'Last Name'
    last_name.admin_order_field = 'contact__last_name'

    def study_group(self):
        if self.contact:
            return self.contact.study_group
        return None
    study_group.short_description = 'Study Group'
    study_group.admin_order_field = 'contact__study_group'
    
    def identity(self):
        return self.connection.identity
    study_group.short_description = 'Identity'
    study_group.admin_order_field = 'connection__identity'
    



