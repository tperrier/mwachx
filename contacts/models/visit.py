#!/usr/bin/python
#Django Imports
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

#Python Imports
import datetime

#Local Imports
from utils.models import TimeStampedModel,ForUserQuerySet
import utils

class SchedualQuerySet(ForUserQuerySet):

    def pending(self):
        return self.filter(arrived=None,skipped=None).active_users()

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
        return self.filter( scheduled_Q & notification_Q)

class ScheduledEvent(TimeStampedModel):

    class Meta:
        abstract = True
        ordering = ('-scheduled',)
        app_label = 'contacts'

    scheduled = models.DateField()
    arrived = models.DateField(blank=True,null=True,default=None)
    notification_last_seen = models.DateField(null=True,default=None)
    notify_count = models.IntegerField(default=0)
    skipped = models.NullBooleanField(default=None)

    participant = models.ForeignKey(settings.MESSAGING_CONTACT)

    def days_overdue(self):
        return (utils.today()-self.scheduled).days

    def days_str(self):
        return self.participant.days_str(today=self.scheduled)

    def is_pregnant(self):
        return self.participant.was_pregnant(today=self.scheduled)

    def seen(self,seen=None):
        ''' Mark visit as seen today '''
        if seen is None:
            seen = utils.today()
        else:
            seen = utils.angular_datepicker(seen)

        self.notify_count += 1
        self.notification_last_seen = seen
        self.save()

    def attended(self,arrived=None):
        ''' Mark visted as attended on @arrived (default today) '''
        if arrived is None:
            arrived = utils.today()
        else:
            arrived = utils.angular_datepicker(arrived)

        self.arrived = arrived
        self.skipped = False
        self.save()

    def skip(self):
        ''' Mark visit as skipped '''
        self.arrived = None
        self.skipped = True
        self.save()

class VisitQuerySet(SchedualQuerySet):

    def get_visit_checks(self):
        visits_this_week = self.pending().visit_range(start={'weeks':0},end={'days':7},notification_start={'days':1})
        bookcheck_weekly = self.pending().visit_range(start={'days':8},end={'days':35},notification_start={'weeks':1})
        bookcheck_monthly = self.pending().visit_range(start={'days':36},notification_start={'weeks':4})

        # print visits_this_week
        return visits_this_week | bookcheck_weekly | bookcheck_monthly

    def top(self):
        return self[:2]

class Visit(ScheduledEvent):

    #Set Custom Manager
    objects = VisitQuerySet.as_manager()

    VISIT_TYPE_CHOICES = (
        ('clinic','Clinic Visit'),
        ('study','Study Visit'),
    )

    # Date Fields

    comment = models.TextField(blank=True,null=True)
    visit_type = models.CharField(max_length=25,choices=VISIT_TYPE_CHOICES,default='clinic')

    def is_bookcheck(self):
        ''' Bookcheck is true for any visit more than 7 days overdue '''
        return self.days_overdue() >= 7

class ScheduledPhoneCallQuerySet(SchedualQuerySet):

    def get_pending_calls(self):
        return self.pending().visit_range(notification_start={'days':2})

class ScheduledPhoneCall(ScheduledEvent):

    objects = ScheduledPhoneCallQuerySet.as_manager()

    CALL_TYPE_OPTIONS = (
        ('m','One Month'),
        ('y','One Year'),
    )

    call_type = models.CharField(max_length=2,choices=CALL_TYPE_OPTIONS,default='m')

    def called(self,outcome,created=None,length=None,comment=None,admin_user=None):

        if outcome == 'answered':
            self.attended(created)
        else:
            self.seen(created)

        # Make a new phone call for participant
        return self.participant.add_call(created=created,outcome=outcome,length=length,comment=comment,
             scheduled=self,admin_user=admin_user)
