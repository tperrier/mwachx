#!/usr/bin/python
#Django Imports
from django.db import models
from django.conf import settings
from jsonfield import JSONField
from django.utils import timezone


#Local Imports
import swapper
from visit import ScheduledPhoneCall
import utils
from utils.models import TimeStampedModel, BaseQuerySet, ForUserQuerySet


class MessageQuerySet(ForUserQuerySet):

    participant_field = 'contact'

    def pending(self):
        return self.filter(is_viewed=False,is_outgoing=False)

    def to_translate(self):
        return self.filter(is_system=False,translation_status='todo')

    def add_success_dt(self):
        return self.annotate(
            success_dt=utils.sqlite_date_diff('created','external_success_time')
        ).order_by('-success_dt')

    def add_study_dt(self):
        return self.annotate(
            study_dt=utils.sqlite_date_diff('contact__created','created',days=True),
            delivery_dt=utils.sqlite_date_diff('contact__delivery_date','created',days=True)
        )


class Message(TimeStampedModel):
    """
    A Message is a message *instance*
    """

    #Set Custom Manager
    objects = MessageQuerySet.as_manager()

    STATUS_CHOICES = (
        ('todo','Todo'),
        ('none','None'),
        ('done','Done'),
        ('auto','Auto'),
        ('cust','Custom'),
    )

    EXTERNAL_CHOICES = (
        ('','Received'),
        ('Success','Success'),
        ('Failed','Failed'),
        ('Sent','Sent'),
        ('Message Rejected By Gateway','Message Rejected By Gateway'),
        ('Could Not Send','Could Not Send')
    )

    class Meta:
        ordering = ('-created',)
        app_label = 'contacts'

    text = models.TextField(help_text='Text of the SMS message')

    #Boolean Flags on Message
    is_outgoing = models.BooleanField(default=True,verbose_name="Out")
    is_system = models.BooleanField(default=True,verbose_name="System")
    is_viewed = models.BooleanField(default=False,verbose_name="Viewed")
    is_related = models.NullBooleanField(default=None,blank=True,null=True)

    parent = models.ForeignKey('contacts.Message',related_name='replies',blank=True,null=True)
    action_time = models.DateTimeField(default=None,blank=True,null=True)

    # translation
    translated_text = models.TextField(max_length=1000,help_text='Text of the translated message',default='',blank=True)
    translation_status = models.CharField(max_length=5,help_text='Status of translation',choices=STATUS_CHOICES,default='todo',verbose_name="Translated")
    translation_time = models.DateTimeField(blank=True,null=True)

    # Meta Data
    languages = models.CharField(max_length=50,help_text='Semi colon seperated list of languages',default='',blank=True)
    topic = models.CharField(max_length=25,help_text='The topic of this message',default='',blank=True)

    admin_user = models.ForeignKey(settings.MESSAGING_ADMIN, blank=True, null=True)
    connection = models.ForeignKey(settings.MESSAGING_CONNECTION)
    contact = models.ForeignKey(swapper.get_model_name('contacts', 'Contact'), blank=True, null=True)

    #Africa's Talking Data Only for outgoing messages
    external_id = models.CharField(max_length=50,blank=True)
    external_success = models.NullBooleanField(verbose_name="Success")
    external_status = models.CharField(max_length=50,blank=True,choices=EXTERNAL_CHOICES)
    external_success_time = models.DateTimeField(default=None,blank=True,null=True)
    external_data = JSONField(blank=True)

    # Description message of system message
    auto = models.CharField(max_length=50,blank=True)

    def is_pending(self):
        return not self.is_viewed and not self.is_outgoing
    is_pending.short_description = 'Pending'

    def is_reply(self):
        return self.parent is not None
    is_reply.short_description = 'Reply'
    is_reply.boolean = True

    def sent_by(self):
        if self.is_outgoing:
            if self.is_system:
                return 'system'
            return 'nurse'
        return 'participant'

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
        self.set_action_time()
        self.save()

    def set_action_time(self):
        if self.action_time is None:
            self.action_time = timezone.now()

    def description(self):
        if self.is_system:
            return self.auto
        return 'none'

    @property
    def study_wk(self):
        return (self.created.date() - self.contact.created.date()).total_seconds() / 604800

    @property
    def edd_wk(self):
        return (self.created.date() - self.contact.due_date).total_seconds() / 604800

    def get_auto(self):
        if self.auto:
            try:
                auto_msg = back.AutomatedMessage.objects.from_description(self.auto)
            except ValueError as e:
                return None
            return auto_msg

    @property
    def display_text(self):
        if self.auto:
            auto_msg = self.get_auto()
            return auto_msg.english if auto_msg is not None else self.auto
        if self.translation_status == 'done':
            return self.translated_text
        else:
            return self.text

    @property
    def auto_type(self):
        if self.auto:
            split = self.auto.split('.')
            if split[0] in ('edd','dd','signup','loss','stop'):
                return '{0[0]}.{0[-1]}'.format(split)
            elif split[0] == 'visit':
                return '{0[0]}.{0[2]}'.format(split)
            elif split[0] == 'bounce':
                return '{0[0]}.{0[1]}'.format(split)

    @property
    def auto_type(self):
        if self.auto:
            split = self.auto.split('.')
            if split[0] in ('edd','dd','signup','loss','stop'):
                return '{0[0]}.{0[3]}'.format(split)
            elif split[0] == 'visit':
                return '{0[0]}.{0[2]}'.format(split)
            elif split[0] == 'bounce':
                return '{0[0]}.{0[1]}'.format(split)

    @property
    def msg_type(self):
        if self.is_outgoing is False:
            try:
                return self.contact.study_group or 'empty_study_group'
            except AttributeError as e:
                return 'anonymous'
        else:
            if self.is_system is True:
                return self.auto.split('.')[0] or 'empty_auto'
            else:
                return self.sent_by()
        return 'end'

    @property
    def previous_outgoing(self):
        try:
            return self._previous_outgoing
        except AttributeError as e:
            self._previous_outgoing = self.contact.message_set.filter(created__lt=self.created,is_outgoing=True).first()
            return self._previous_outgoing

class PhoneCallQuerySet(ForUserQuerySet):

    participant_field = 'contact'

class PhoneCall(TimeStampedModel):
    """
    A PhoneCall represents the *log* of a call made.
    Phone call objects are entered manually and the actual calls are made outside of the Mwach system.
    """

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
    contact = models.ForeignKey(swapper.get_model_name('contacts', 'Contact'))
    admin_user = models.ForeignKey(settings.MESSAGING_ADMIN, blank=True, null=True)

    is_outgoing = models.BooleanField(default=False)
    outcome = models.CharField(max_length=10,choices=OUTCOME_CHOICES,default='answered')
    length = models.IntegerField(blank=True,null=True)
    comment = models.TextField(blank=True,null=True)

    # Link to scheduled phone call field
    scheduled = models.ForeignKey(ScheduledPhoneCall,blank=True,null=True)


class Note(TimeStampedModel):

    class Meta:
        ordering = ('-created',)
        app_label = 'contacts'

    objects = BaseQuerySet.as_manager()

    participant = models.ForeignKey(swapper.get_model_name('contacts', 'Contact'))
    admin = models.ForeignKey(settings.MESSAGING_ADMIN, blank=True, null=True)
    comment = models.TextField(blank=True)

    def is_pregnant(self):
        return self.participant.was_pregnant(today=self.created.date())
