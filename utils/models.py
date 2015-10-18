# Python Imports

# Django Imports
from django.db import models
from django.core.exceptions import ObjectDoesNotExist, FieldError
from django.utils import timezone
# Create your models here.

class TimeStampedModel(models.Model):

    class Meta:
        ordering = ['-created']

    #The date and time this message was created or modified
    created = models.DateTimeField(default=timezone.now)
    modified = models.DateTimeField(auto_now=True)

    def created_str(self,format='%Y-%m-%d %H:%M'):
        return self.created.strftime(format)

    class Meta:
        abstract = True

class BaseQuerySet(models.QuerySet):

    def get_or_none(self,**kwargs):
        return self.get_or_default(None,**kwargs)

    def get_or_default(self,default=None,**kwargs):
        try:
            return self.get(**kwargs)
        except ObjectDoesNotExist:
            return default

class ForUserQuerySet(BaseQuerySet):

    def for_user(self,user):
        try:
            return self.filter(contact__facility=user.practitioner.facility)
        except FieldError as e:
            try:
                return self.filter(participant__facility=user.practitioner.facility)
            except (ObjectDoesNotExist, AttributeError) as e:
                return self.none()
        except (ObjectDoesNotExist, AttributeError) as e:
            return self.none()
