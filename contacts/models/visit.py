#!/usr/bin/python
#Django Imports
from django.db import models
from django.conf import settings

#Local Imports
from utils.models import TimeStampedModel


class Visit(TimeStampedModel):
    class Meta:
        ordering = ('scheduled',)
    
    contact = models.ForeignKey(settings.MESSAGING_CONTACT)
    parent = models.ForeignKey('self', related_name='children_set', null=True, blank=True, default=None)
    scheduled = models.DateField()
    arrived = models.DateField(blank=True,null=True,default=None)
    skipped = models.NullBooleanField(default=None)
    comment = models.CharField(max_length=500,blank=True,null=True)
    
    def study_id(self):
        return self.contact.id
    study_id.short_description = 'Study ID'
    study_id.admin_order_field = 'contact__study_id'
    
    def contact_name(self):
        return self.contact.nickname
    contact_name.short_description = 'Nickname'
    contact_name.admin_order_field = 'contact__nickname'
    
    @property
    def original(self):
        return self.parent.scheduled if self.parent else self.scheduled

    @property
    def overdue(self):
        today = settings.CURRENT_DATE
        return (today-self.original).days
