#!/usr/bin/python
#Django Imports
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

#Local Imports
from utils.models import TimeStampedModel, BaseQuerySet

class MessageQuerySet(BaseQuerySet):
    
    def pending(self):
        return self.filter(is_viewed=False)
        
    def to_translate(self):
        return self.filter(is_system=False).filter(Q(translation=None)|Q(translation__is_complete=False))
        
    def for_user(self,user):
        try:
            return self.filter(contact__facility=user.practitioner.facility)
        except ObjectDoesNotExist:
            return self

class Language(TimeStampedModel):
    short_name = models.CharField(max_length=1)
    name = models.CharField(max_length=20)

    messages = models.ManyToManyField("Message",blank=True, null=True)
    
class Translation(TimeStampedModel):

    text = models.CharField(max_length=1000,help_text='Text of the translated message')

    is_complete = models.BooleanField(default=False)
    is_skipped = models.BooleanField(default=False)
    
    @property
    def parent(self):
        try:
            return self.message.text
        except Translate.DoesNotExist:
            return ''
            


class Message(TimeStampedModel):
    class Meta:
        ordering = ('-created',)
    
    text = models.CharField(max_length=1000,help_text='Text of the SMS message')

    #Set Custom Manager
    objects = MessageQuerySet.as_manager()
    
    #Boolean Flags on Message
    is_outgoing = models.BooleanField(default=True)
    is_system = models.BooleanField(default=True)
    is_viewed = models.BooleanField(default=False)
    
    # ToDo:Link To Automated Message
    parent = models.ForeignKey('contacts.Message',related_name='replies',blank=True,null=True)
    
    translation = models.OneToOneField('contacts.Translation',blank=True,null=True)

    admin_user = models.ForeignKey(settings.MESSAGING_ADMIN, blank=True, null=True)
    connection = models.ForeignKey(settings.MESSAGING_CONNECTION)
    contact = models.ForeignKey(settings.MESSAGING_CONTACT,blank=True,null=True)
    
    def get_real_text(self):
        return self.translation.text if self.is_translated() else self.text

    def get_original_text(self):
        return self.text
        
    def is_translated(self):
        return self.translation.is_complete if self.translation else False

    def lang_ids(self):
        return [l.id for l in self.language_set.all()]

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
    
    def weeks(self):
        return self.contact.weeks(today=self.created.date())
        
    def is_pregnant(self):
        return self.contact.was_pregnant(today=self.created.date())
    
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
    def send(contact,message,is_system=True,parent=None):
        Message.objects.create(
            is_system=is_system,
            text=message,
            connection=contact.connection,
            contact=contact,
            is_viewed=True,
            parent=parent,
        )
