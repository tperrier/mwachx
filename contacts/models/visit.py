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

    def get_upcoming(self):
        return self.visit_range(start={'weeks':0},end={'days':7},notification_start={'days':1})

    def get_bookcheck(self):
        bookcheck_weekly = self.visit_range(start={'days':8},end={'days':35},notification_start={'weeks':1})
        bookcheck_monthly = self.visit_range(start={'days':36},notification_start={'weeks':4})
        return bookcheck_weekly | bookcheck_monthly

    def pending(self):
        return self.filter(arrived=None,skipped=None)

    def visit_range(self,start,end=None,notification_start=None,notification_end=None):
        today = utils.today()
        start = today - datetime.timedelta(**start)
        notification_start = today - datetime.timedelta(**notification_start)
        print today,start
        if end is not None:
            end = today - datetime.timedelta(**end)
            if notification_end is not None:
                notification_end = today - datetime.timedelta(**notification_end)
                # return self.pending().filter(scheduled__range=(end,start), notification_last_seen__range=(notification_end,notification_start))
                return self.pending().filter(scheduled__range=(end,start))
            # return self.pending().filter(scheduled__range=(end,start), notification_last_seen__lte=notification_start)
            return self.pending().filter(scheduled__range=(end,start))
        else:
            if notification_end is not None:
                notification_end = today - datetime.timedelta(**notification_end)
                return self.pending().filter(scheduled__lte=start, notification_last_seen__range=(notification_end,notification_start))
        return self.pending().filter(scheduled__lte=start, notification_last_seen__lte=notification_start)

    def for_user(self,user):
        try:
            return self.filter(participant__facility=user.practitioner.facility)
        except (ObjectDoesNotExist, AttributeError) as e:
            return self

    def top(self):
        return self[:2]

class Visit(TimeStampedModel):

    #Set Custom Manager
    objects = VisitQuerySet.as_manager()

    VISIT_TYPE_CHOICES = (
        ('clinic','Clinic Visit'),
        ('study','Study Visit'),
    )

    class Meta:
        ordering = ('-scheduled',)
        app_label = 'contacts'

    # Date Fields
    scheduled = models.DateField()
    arrived = models.DateField(blank=True,null=True,default=None)
    notification_last_seen = models.DateField(null=True,default=None)
    skipped = models.NullBooleanField(default=None)

    participant = models.ForeignKey(settings.MESSAGING_CONTACT)
    comment = models.CharField(max_length=500,blank=True,null=True,default=None)

    visit_type = models.CharField(max_length=25,choices=VISIT_TYPE_CHOICES,default='clinic')

    def study_id(self):
        return self.participant.id
    study_id.short_description = 'Study ID'
    study_id.admin_order_field = 'contact__study_id'

    def contact_name(self):
        return self.participant.nickname
    contact_name.short_description = 'Nickname'
    contact_name.admin_order_field = 'contact__nickname'

    def days_overdue(self):
        return (utils.today()-self.scheduled).days
