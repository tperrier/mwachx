#!/usr/bin/python
#Django Imports
from django.db import models
from django.conf import settings

#Local Imports
from utils.models import TimeStampedModel,BaseQuerySet
from contacts.models import Contact

class PhoneCall(TimeStampedModel):
    
    class Meta:
        ordering = ('-created',)
    
    objects = BaseQuerySet.as_manager()
    
    contact = models.ForeignKey(settings.MESSAGING_CONTACT)
    answered = models.BooleanField(default=False)
    incomming = models.BooleanField(default=True)
    comment = models.CharField(max_length=500,blank=True,null=True)
    
class Note(TimeStampedModel):
    
    class Meta:
        ordering = ('-created',)
    
    objects = BaseQuerySet.as_manager()
     
    contact = models.ForeignKey(settings.MESSAGING_CONTACT)
    admin = models.ForeignKey(settings.MESSAGING_ADMIN, blank=True, null=True)
    comment = models.CharField(max_length=500,blank=True,null=True)
    
class Connection(models.Model):
    
    objects = BaseQuerySet.as_manager()
    
    TYPE_CHOICES = (
        ('phone','Phone Number'),
        ('email','Email'),
    )
    
    identity = models.CharField(max_length=25,primary_key=True)
    contact = models.ForeignKey(settings.MESSAGING_CONTACT,blank=True,null=True)
    
    description = models.CharField(max_length=150,blank=True,null=True,help_text='Description of phone numbers relationship to contact')
    connection_type = models.CharField(max_length=10,help_text='Type of connection',default='phone')
    
    is_primary = models.BooleanField(default=False)

class StatusChange(TimeStampedModel):
    
    objects = BaseQuerySet.as_manager()
    
    class Meta:
        ordering = ('-created',)
    
    contact = models.ForeignKey(settings.MESSAGING_CONTACT)
    old = models.CharField(max_length=20,choices=Contact.STATUS_CHOICES)
    new = models.CharField(max_length=20,choices=Contact.STATUS_CHOICES)
    
class Facility(models.Model):
    
    class Meta:
        verbose_name_plural = 'facilities'
    
    name = models.CharField(max_length='50',help_text='Facility Name')
    
    def __str__(self):
        return self.name
    
    
    
