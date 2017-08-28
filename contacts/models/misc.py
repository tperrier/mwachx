
#!/usr/bin/python
#Django Imports
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from jsonfield import JSONField

#Local Imports
import transports
from utils.models import TimeStampedModel,BaseQuerySet

class Connection(models.Model):

    class Meta:
        app_label = 'contacts'

    objects = BaseQuerySet.as_manager()

    identity = models.CharField(max_length=25,primary_key=True)
    contact = models.ForeignKey(settings.MESSAGING_CONTACT,blank=True,null=True)

    description = models.CharField(max_length=30,blank=True,null=True,help_text='Description of phone numbers relationship to contact')

    is_primary = models.BooleanField(default=False,verbose_name='Primary')

    def __unicode__(self):
        return "{} ({})".format(self.contact.study_id if self.contact else '',self.identity)

    def send_custom(self,text,translated_text='',languages='',**kwargs):

        return self.send_message(text,translation_status='cust',translated_text=translated_text,languages=languages,is_system=False,**kwargs)

    def send_message(self,text,**kwargs):

        # Send message over system transport
        try:
            msg_id, msg_success, external_data = transports.send(self.identity,text)
        except transports.TransportError as e:
            msg_id = ""
            msg_success = False
            external_data = {"error":str(e)}

        # Create new message
        new_message = self.message_set.create(
            text=text,
            connection=self,
            external_id=msg_id,
            external_success=msg_success,
            external_status="Sent" if msg_success else external_data.get("status","Failed"),
            external_data=external_data,
            **kwargs)

        return new_message

class PractitionerQuerySet(BaseQuerySet):

    def for_participant(self,participant):
        return self.filter(facility=participant.facility).exclude(user__first_name='').select_related('user').first()

class Practitioner(models.Model):
    '''
    User profile for nurse practitioners to link a User profile to a Facility
    '''
    class Meta:
        app_label = 'contacts'

    objects = PractitionerQuerySet.as_manager()

    user = models.OneToOneField(User)
    facility = models.CharField(max_length=15,choices=settings.FACILITY_CHOICES)
    password_changed = models.BooleanField(default=False)

    @property
    def username(self):
        return self.user.username

    def __str__(self):
        return '{0}'.format(self.user.username)

    def __repr__(self):
        return '<{0!s}> <{1}>'.format(self.facility,self.user.username)

class EventLog(TimeStampedModel):

    class Meta:
        app_label = 'contacts'

    objects = BaseQuerySet.as_manager()

    user = models.ForeignKey(User)
    event = models.CharField(max_length=25,help_text="Event Name")
    data = JSONField()
