
#!/usr/bin/python
#Django Imports
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from jsonfield import JSONField

#Local Imports
from utils.models import TimeStampedModel,BaseQuerySet

class Connection(models.Model):

    class Meta:
        app_label = 'contacts'

    objects = BaseQuerySet.as_manager()

    identity = models.CharField(max_length=25,primary_key=True)
    contact = models.ForeignKey(settings.MESSAGING_CONTACT,blank=True,null=True)

    description = models.CharField(max_length=30,blank=True,null=True,help_text='Description of phone numbers relationship to contact')

    is_primary = models.BooleanField(default=False)

    def __unicode__(self):
        return "{} ({})".format(self.contact.study_id if self.contact else '',self.identity)

class Practitioner(models.Model):
    '''
    User profile for nurse practitioners to link a User profile to a Facility
    '''
    class Meta:
        app_label = 'contacts'

    objects = BaseQuerySet.as_manager()

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
