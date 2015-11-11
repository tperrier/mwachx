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

    def for_user(self,user, superuser=False):
        if superuser and user.is_superuser:
            return self.all()

        # Get facility or return no participants if there is no facility
        try:
            facility = user.practitioner.facility
        except (ObjectDoesNotExist) as e:
            return self.none()

        # Try to filter by facility using contact, participant or self
        filter = _try_filter(self,models.Q(contact__facility=facility))
        if filter is None:
            filter = _try_filter(self,models.Q(participant__facility=facility))
        if filter is None:
            filter = _try_filter(self,models.Q(facility=facility))

        return filter if filter is not None else self.none()

def _try_filter(queryset,q):
    try:
        return queryset.filter(q)
    except FieldError as e:
        return None
