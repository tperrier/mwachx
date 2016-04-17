# Python Imports

# Django Imports
from django.db import models
from django.core.exceptions import ObjectDoesNotExist, FieldError
from django.utils import timezone
# Create your models here.

class TimeStampedModel(models.Model):

    #The date and time this message was created or modified
    created = models.DateTimeField(default=timezone.now,editable=False)
    modified = models.DateTimeField(auto_now=True)

    def created_str(self,format='%Y-%m-%d %H:%M'):
        return self.created.strftime(format)

    class Meta:
        abstract = True
        ordering = ['-created']

class BaseQuerySet(models.QuerySet):

    def get_or_none(self,**kwargs):
        return self.get_or_default(None,**kwargs)

    def get_or_default(self,default=None,**kwargs):
        try:
            return self.get(**kwargs)
        except ObjectDoesNotExist:
            return default

class ForUserQuerySet(BaseQuerySet):

    NO_SMS_STATUS = ('stopped','other','sae','quit')
    NOT_ACTIVE_STATUS = NO_SMS_STATUS + ('completed',)
    participant_field = 'participant'

    def for_user(self,user, superuser=False):
        if superuser and user.is_superuser:
            return self.all()

        # Get facility or return no participants if there is no facility
        try:
            facility = user.practitioner.facility
        except (ObjectDoesNotExist) as e:
            return self.none()

        return self.by_facility(facility)

    def by_facility(self,facility):
        return self.filter(self.participant_Q(facility=facility))

    def active_users(self):
        ''' Filter queryset based on active users who should receive SMS messages.'''
        q = self.participant_Q(status__in=ForUserQuerySet.NO_SMS_STATUS)
        return self.exclude(q)

    def pregnant(self):
        q = self.participant_Q(status__in=('pregnant','over'))
        return self.filter(q)

    def post_partum(self):
        q = self.participant_Q(status__in=('post','ccc'))
        return self.filter(q)

    def participant_Q(self,**kwargs):
        ''' Return a Q object with participant_field appended
        Example:  participant_Q(study_group='two-way',is_validated=False)
            returns: Q(participant__study_group='two-way',participant__is_validated=False)
        '''
        prefix = self.participant_field+'__' if self.participant_field is not None else ''
        kwargs = {prefix+key:value for key,value in kwargs.items()}
        return models.Q(**kwargs)
