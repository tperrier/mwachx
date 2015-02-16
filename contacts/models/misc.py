#!/usr/bin/python
#Django Imports
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

#Local Imports
from utils.models import TimeStampedModel,BaseQuerySet
from contacts.models import Contact

class PhoneCallQuerySet(BaseQuerySet):
    
    def for_user(self,user):
        try:
            return self.filter(contact__facility=user.practitioner.facility)
        except ObjectDoesNotExist:
            return self


class PhoneCall(TimeStampedModel):
    
    class Meta:
        ordering = ('-created',)
    
    objects = PhoneCallQuerySet.as_manager()
    
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
        #Change kisumu_east to Kisumu East
        return ' '.join([word.capitalize() for word in self.name.split('_')])
        
class Practitioner(models.Model):
    '''
    User profile for nurse practitioners to link a User profile to a Facility
    '''
    user = models.OneToOneField(User)
    facility = models.ForeignKey('contacts.Facility')
    
    @property
    def username(self):
        return self.user.username
        
    def __str__(self):
        return '<{}> <{}>'.format(self.facility,self.user.username)
    
    
    
