#!/usr/bin/python
#Django Imports
from django.db import models
from django.conf import settings

#Python Imports
import datetime

#Local Imports
from utils.models import TimeStampedModel,BaseQuerySet

class VisitQuerySet(BaseQuerySet):

    def pending(self):
        return self.filter(arrived=None,skipped=None)
    
    def visit_range(self,start,end=None,reminder_start=None,reminder_end=None):
        today = settings.CURRENT_DATE
        start = today - datetime.timedelta(**start)
        reminder_start = today - datetime.timedelta(**reminder_start)
        if end is not None:
            end = today - datetime.timedelta(**end) 
            if reminder_end is not None:
                reminder_end = today - datetime.timedelta(**reminder_end)
                return self.pending().filter(scheduled__range=(end,start), reminder_last_seen__range=(reminder_end,reminder_start))
            return self.pending().filter(scheduled__range=(end,start), reminder_last_seen__lte=reminder_start)    
        else:
            if reminder_end is not None:
                reminder_end = today - datetime.timedelta(**reminder_end)
                return self.pending().filter(scheduled__lte=start, reminder_last_seen__range=(reminder_end,reminder_start))
        return self.pending().filter(scheduled__lte=start, reminder_last_seen__lte=reminder_start)

class Visit(TimeStampedModel):
    class Meta:
        ordering = ('scheduled',)
    
    #Set Custom Manager
    objects = VisitQuerySet.as_manager()
    
    contact = models.ForeignKey(settings.MESSAGING_CONTACT)
    parent = models.ForeignKey('self', related_name='children_set', null=True, blank=True, default=None)
    reminder_last_seen = models.DateField(null=True)
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
    def days_overdue(self):
        today = settings.CURRENT_DATE
        return (today-self.scheduled).days

    @staticmethod
    def new_visit(contact,scheduled,reminder_last_seen=None,parent=None,arrived=None,skipped=None,comment=None,):
        Visit.objects.create(
            contact=contact,
            scheduled=scheduled,
            parent=parent,
            reminder_last_seen=reminder_last_seen,
            arrived=arrived,
            skipped=skipped,
            comment=comment,
        )