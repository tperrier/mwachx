#!/usr/bin/python
#Django Imports
from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

#Python Imports
import datetime

#Local Imports
from utils.models import TimeStampedModel,BaseQuerySet
import utils

class VisitQuerySet(BaseQuerySet):
    
    def get_upcoming_visits(self):
        return self.visit_range(start={'weeks':0},end={'days':7},reminder_start={'days':1})

    def get_bookcheck(self):
        bookcheck_weekly = self.visit_range(start={'days':8},end={'days':35},reminder_start={'weeks':1})
        bookcheck_monthly = self.visit_range(start={'days':36},reminder_start={'weeks':4})
        return bookcheck_weekly | bookcheck_monthly

    def pending(self):
        return self.filter(arrived=None,skipped=None)
    
    def visit_range(self,start,end=None,reminder_start=None,reminder_end=None):
        today = utils.today()
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
        
    def for_user(self,user):
        try:
            return self.filter(contact__facility=user.practitioner.facility)
        except ObjectDoesNotExist:
            return self

class Visit(TimeStampedModel):
    VISIT_TYPE_CHOICES = (
        ('clinic','Clinic Visit'),
        ('study','Study Visit'),
    )

    class Meta:
        ordering = ('-scheduled',)
    
    #Set Custom Manager
    objects = VisitQuerySet.as_manager()
    
    contact = models.ForeignKey(settings.MESSAGING_CONTACT)
    parent = models.ForeignKey('self', related_name='children_set', null=True, blank=True, default=None)
    reminder_last_seen = models.DateField(null=True,default=None)
    scheduled = models.DateField()
    arrived = models.DateField(blank=True,null=True,default=None)
    skipped = models.NullBooleanField(default=None)
    comment = models.CharField(max_length=500,blank=True,null=True,default=None)
    
    visit_type = models.CharField(max_length=25,choices=VISIT_TYPE_CHOICES,null=False,blank=False)

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
        return (utils.today()-self.scheduled).days
