#!/usr/bin/python
#Django Imports
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

#Python Imports
import datetime

#Local Imports
from utils.models import TimeStampedModel,BaseQuerySet
import utils

class VisitQuerySet(BaseQuerySet):

    def get_visit_checks(self):
        visits_this_week = self.visit_range(start={'weeks':0},end={'days':7},notification_start={'days':1})
        bookcheck_weekly = self.visit_range(start={'days':8},end={'days':35},notification_start={'weeks':1})
        bookcheck_monthly = self.visit_range(start={'days':36},notification_start={'weeks':4})

        return visits_this_week | bookcheck_weekly | bookcheck_monthly

    def pending(self):
        return self.filter(arrived=None,skipped=None)

    def visit_range(self,start={'days':0},end=None,notification_start={'days':0},notification_end=None):
        today = utils.today()
        start = today - datetime.timedelta(**start)
        notification_start = today - datetime.timedelta(**notification_start)

        if end is not None:
            end = today - datetime.timedelta(**end)
            scheduled_Q = Q(scheduled__range=(end,start))
        else:
            scheduled_Q = Q(scheduled__lte=start)

        if notification_end is not None:
            notification_end = today - datetime.timedelta(**notification_end)
            notification_Q = Q(notification_last_seen__range=(notification_end,notification_start))
        else:
            notification_Q = Q(notification_last_seen__lte=notification_start)

        notification_Q |= Q(notification_last_seen__isnull=True)
        return self.pending().filter( scheduled_Q & notification_Q)

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
    notify_count = models.IntegerField(default=0)
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

    def is_bookcheck(self):
        ''' Bookcheck is true for any visit more than 7 days overdue '''
        return self.days_overdue() >= 7

    def seen(self):
        ''' Mark visit as seen today '''
        self.notify_count += 1
        self.notification_last_seen = utils.today()
        self.save()

    def attended(self,arrived=None):
        ''' Mark visted as attended on @arrived (default today) '''
        self.arrived = arrived if arrived is not None else utils.today()
        self.skipped = False
        self.save()

    def skip(self):
        ''' Mark visit as skipped '''
        self.arrived = None
        self.skipped = True
        self.save()
