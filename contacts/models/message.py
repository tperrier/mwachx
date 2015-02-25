#!/usr/bin/python
#Django Imports
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from constance import config

#Local Imports
from utils.models import TimeStampedModel, BaseQuerySet

class MessageQuerySet(BaseQuerySet):
    
    def pending(self):
        return self.filter(is_viewed=False)
        
    def to_translate(self):
        return self.filter(is_system=False,is_translated=False,translate_skipped=False)
        
    def for_user(self,user):
        try:
            return self.filter(contact__facility=user.practitioner.facility)
        except ObjectDoesNotExist:
            return self

class Language(TimeStampedModel):
    short_name = models.CharField(max_length=1)
    name = models.CharField(max_length=20)

    messages = models.ManyToManyField("Message",related_name='languages',blank=True, null=True)

    def __str__(self):
        return self.short_name

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
    is_related = models.NullBooleanField(default=None,blank=True,null=True)
    
    # ToDo:Link To Automated Message
    parent = models.ForeignKey('contacts.Message',related_name='replies',blank=True,null=True)
    
    # translation
    translated_text = models.CharField(max_length=1000,help_text='Text of the translated message',default=None,blank=True,null=True)
    is_translated = models.BooleanField(default=False)
    translate_skipped = models.BooleanField(default=False)

    topic = models.CharField(max_length=50,help_text='The topic of this message',default=None,blank=True,null=True)
    
    admin_user = models.ForeignKey(settings.MESSAGING_ADMIN, blank=True, null=True)
    connection = models.ForeignKey(settings.MESSAGING_CONNECTION)
    contact = models.ForeignKey(settings.MESSAGING_CONTACT,blank=True,null=True)

    #Africa's Talking Data
    #ToDo: make this a data field once we know the format
    time_received = models.CharField(max_length=50,default=None,blank=True,null=True)
    external_id = models.CharField(max_length=50,default=None,blank=True,null=True)
    external_linkId = models.CharField(max_length=50,default=None,blank=True,null=True)
    
    def get_real_text(self):
        return self.translated_text if self.is_translated else self.text

    def get_original_text(self):
        return self.text
        
    def translation_skipped(self):
        return self.translate_skipped

    def is_translation_pending(self):
        return (not self.is_translated) and (not self.is_system)

    def is_pending(self):
        return not self.is_viewed and not self.is_outgoing

    def lang_ids(self):
        return [l.id for l in self.languages.all()]

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

    def languages_str(self):
        return ','.join([str(l) for l in self.languages.all()])
    
    @staticmethod
    def receive(number,message,time_received,external_id,external_linkId):
        '''
        Main hook for receiving messages
            * number: the phone number of the incoming message
            * message: the text of the incoming message
        '''
        from contacts.models import Connection
        #Get incoming connection
        connection,created = Connection.objects.get_or_create(identity=number)
        contact = None if created else connection.contact
        Message.objects.create(
            is_system=False,
            is_outgoing=False,
            text=message,
            connection=connection,
            contact=contact,
            time_received=time_received,
            external_id=external_id,
            external_linkId=external_linkId
        )
        
    @staticmethod
    def send(contact,message,translation,is_translated=False,translate_skipped=False,is_system=True,parent=None,languages=None):
        
        if config.AFRICAS_TALKING_SEND:
            import africas_talking
            try:
                africas_talking.send(contact.connection.identity,message)
            except africas_talking.AfricasTalkingException as e:
                pass

        _msg = Message.objects.create(
            is_system=is_system,
            text=message,
            translated_text=translation,
            is_translated=is_translated,
            translate_skipped=translate_skipped,
            connection=contact.connection,
            contact=contact,
            is_viewed=True,
            parent=parent,
        )
        if languages:
            lang_objs = Language.objects.filter(id__in=languages)
            _msg.languages = lang_objs
            _msg.save()
