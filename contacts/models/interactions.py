#!/usr/bin/python
#Django Imports
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from jsonfield import JSONField

from constance import config

#Local Imports
from visit import ScheduledPhoneCall
from utils.models import TimeStampedModel, BaseQuerySet, ForUserQuerySet

class MessageQuerySet(ForUserQuerySet):

    participant_field = 'contact'

    def pending(self):
        return self.filter(is_viewed=False,is_outgoing=False)

    def to_translate(self):
        return self.filter(is_system=False,translation_status='todo')

class Message(TimeStampedModel):

    #Set Custom Manager
    objects = MessageQuerySet.as_manager()

    STATUS_CHOICES = (
        ('todo','Todo'),
        ('none','None'),
        ('done','Done'),
        ('auto','Auto'),
    )

    class Meta:
        ordering = ('-created',)
        app_label = 'contacts'

    text = models.TextField(help_text='Text of the SMS message')

    #Boolean Flags on Message
    is_outgoing = models.BooleanField(default=True)
    is_system = models.BooleanField(default=True)
    is_viewed = models.BooleanField(default=False)
    is_related = models.NullBooleanField(default=None,blank=True,null=True)

    parent = models.ForeignKey('contacts.Message',related_name='replies',blank=True,null=True)

    # translation
    translated_text = models.TextField(max_length=1000,help_text='Text of the translated message',default='',blank=True)
    translation_status = models.CharField(max_length=5,help_text='Status of translation',choices=STATUS_CHOICES,default='todo')

    # Meta Data
    languages = models.CharField(max_length=50,help_text='Semi colon seperated list of languages',default='',blank=True)
    topic = models.CharField(max_length=10,help_text='The topic of this message',default='',blank=True)

    admin_user = models.ForeignKey(settings.MESSAGING_ADMIN, blank=True, null=True)
    connection = models.ForeignKey(settings.MESSAGING_CONNECTION)
    contact = models.ForeignKey(settings.MESSAGING_CONTACT,blank=True,null=True)

    #Africa's Talking Data Only for outgoing messages
    external_id = models.CharField(max_length=50,blank=True)
    external_success = models.NullBooleanField()
    external_data = JSONField()

    # Only for system messages
    auto = models.CharField(max_length=50,blank=True)

    def is_pending(self):
        return not self.is_viewed and not self.is_outgoing

    def sent_by(self):
        if self.is_outgoing:
            if self.is_system:
                return 'system'
            return 'nurse'
        return 'participant'

    def study_id(self):
        if self.contact:
            return self.contact.study_id
        return None
    study_id.short_description = 'Study ID'
    study_id.admin_order_field = 'contact__study_id'

    def contact_name(self):
        if self.contact:
            return '<a href="../contact/{0.study_id}">{0.nickname}</a>'.format(self.contact)
        return None
    contact_name.short_description = 'Contact Name'
    contact_name.admin_order_field = 'contact__nickname'
    contact_name.allow_tags = True

    def identity(self):
        return self.connection.identity
    identity.short_description = 'Identity'
    identity.admin_order_field = 'connection__identity'

    def days_str(self):
        return self.contact.days_str(today=self.created.date())

    def is_pregnant(self):
        return self.contact.was_pregnant(today=self.created.date())

    def dismiss(self,is_related=None,topic='',**kwargs):
		if is_related is not None:
			self.is_related = is_related
		if topic != '':
			self.topic = topic
		self.is_viewed = True
		self.save()

class PhoneCallQuerySet(ForUserQuerySet):

    participant_field = 'contact'

class PhoneCall(TimeStampedModel):

    class Meta:
        ordering = ('-created',)
        app_label = 'contacts'

    OUTCOME_CHOICES = (
        ('no_ring','No Ring'),
        ('no_answer','No Answer'),
        ('answered','Answered'),
    )

    objects = PhoneCallQuerySet.as_manager()

    connection = models.ForeignKey(settings.MESSAGING_CONNECTION)
    contact = models.ForeignKey(settings.MESSAGING_CONTACT)
    admin_user = models.ForeignKey(settings.MESSAGING_ADMIN, blank=True, null=True)

    is_outgoing = models.BooleanField(default=False)
    outcome = models.CharField(max_length=10,choices=OUTCOME_CHOICES,default='answered')
    length = models.IntegerField(blank=True,null=True)
    comment = models.TextField(blank=True,null=True)

    # Link to scheduled phone call field
    scheduled = models.ForeignKey(ScheduledPhoneCall,blank=True,null=True)

    def contact_name(self):
        if self.contact:
            return '<a href="../contact/{0.study_id}">{0.nickname}</a>'.format(self.contact)
        return None
    contact_name.short_description = 'Contact Name'
    contact_name.admin_order_field = 'contact__nickname'
    contact_name.allow_tags = True

class Note(TimeStampedModel):

    class Meta:
        ordering = ('-created',)
        app_label = 'contacts'

    objects = BaseQuerySet.as_manager()

    participant = models.ForeignKey(settings.MESSAGING_CONTACT)
    admin = models.ForeignKey(settings.MESSAGING_ADMIN, blank=True, null=True)
    comment = models.TextField(blank=True)

    def is_pregnant(self):
        return self.participant.was_pregnant(today=self.created.date())
