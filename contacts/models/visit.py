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

    def pending(self,**kwargs):
        pending = self.filter(arrived__isnull=True,status='pending')
        if not kwargs:
            return pending
        pending_Q = Q(**kwargs)
        return pending.filter(pending_Q)

    def is_active(self):
        ''' exclude those participants who's visits we should ignore '''
        return self.exclude(participant__status__in=('completed','quit'))

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

    STATUS_CHOICES = (
        ('pending','Pending'),
        ('missed','Missed'),
        ('deleted','Deleted'),
        ('attended','Attended'),
    )

    class Meta:
        abstract = True
        ordering = ('-scheduled',)
        app_label = 'contacts'

    scheduled = models.DateField()
    arrived = models.DateField(blank=True,null=True,default=None)
    notification_last_seen = models.DateField(null=True,blank=True,default=None)
    notify_count = models.IntegerField(default=0)
    # skipped = models.NullBooleanField(default=None)
    status = models.CharField(max_length=15,choices=STATUS_CHOICES,default='pending',help_text='current status of event')

    participant = models.ForeignKey(settings.MESSAGING_CONTACT)

    def days_overdue(self):
        if self.status == 'pending':
            return (utils.today() - self.scheduled).days
        return 0

    def days_str(self):
        delta_days = -1 * (utils.today() - self.scheduled).days
        if self.status == 'attended' and self.arrived is not None:
            delta_days = (utils.today() - self.arrived).days
        return utils.days_as_str(delta_days)

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

        self.set_status('attended',arrived)

    def set_status(self,status,arrived=None):
        ''' Mark scheduled event status '''
        if arrived is not None:
            self.arrived = arrived
        self.status = status
        self.save()

    def __str__(self):
        return str(self.scheduled)

    def __repr__(self):
        return "{} {}".format(self.scheduled,self.participant)

class VisitQuerySet(SchedualQuerySet):

    def get_visit_checks(self):
        """ Return upcoming visits
            - this_week: not seen today and visit is this week
            - weekly: between 1-5 weeks away and not seen this week
            - monthly: after 5 weeks and not seen for four weeks
        """
        visits_this_week = self.pending().is_active().visit_range(
            start={'weeks':0},end={'days':7},notification_start={'days':1}
        )
        bookcheck_weekly = self.pending().is_active().visit_range(
            start={'days':8},end={'days':35},notification_start={'weeks':1}
        )
        # # Don't think we need this since visits will be missed
        # bookcheck_monthly = self.pending().visit_range(
        #     start={'days':36},notification_start={'weeks':4}
        # )

        # print visits_this_week
        return visits_this_week | bookcheck_weekly

    def get_missed_visits(self,date=None,delta_days=3):
        """ Return pending visits that are 3 days late and have been seen or it has been 3 days
            since an SMS reminder was sent and has been seen more than three times"""
        today = utils.today(date)
        late = today - datetime.timedelta(days=delta_days)

        first_reminder_Q = Q(scheduled__lte=late,notify_count__gt=0,missed_sms_count=0)
        second_reminder_Q = Q(missed_sms_last_sent__lte=late,notify_count__gt=3,missed_sms_count__gt=0)
        return self.pending().is_active().filter(first_reminder_Q | second_reminder_Q)

    def to_send(self):
        return self.exclude(visit_type__in=Visit.NO_SMS_STATUS)

    def top(self):
        return self[:2]

class Visit(ScheduledEvent):

    #Set Custom Manager
    objects = VisitQuerySet.as_manager()

    VISIT_TYPE_CHOICES = (
        ('clinic','Clinic Visit'),
        ('study','Study Visit'),
        ('both','Both'),
        ('delivery','Delivery'),
    )
    NO_SMS_STATUS = ('study','delivery')

    # Custom Visit Fields
    comment = models.TextField(blank=True,null=True)
    visit_type = models.CharField(max_length=25,choices=VISIT_TYPE_CHOICES,default='clinic')

    missed_sms_last_sent = models.DateField(null=True,blank=True,default=None)
    missed_sms_count = models.IntegerField(default=0)

    def send_visit_reminder(self,send=True,extra_kwargs=None):
        if self.no_sms:
            return

        if extra_kwargs is None:
            scheduled_date = datetime.date.today() + datetime.timedelta(days=2)
            extra_kwargs = {'days':2,'date':scheduled_date.strftime('%b %d')}
        condition = self.get_condition('pre')

        return self.participant.send_automated_message(send=send,send_base='visit',
                    condition=condition,extra_kwargs=extra_kwargs)

    def send_missed_visit_reminder(self,send=True):
        if self.no_sms:
            return

        condition = self.get_condition('missed')

        if send is True:
            self.missed_sms_count += 1
            self.missed_sms_last_sent = datetime.date.today()
            if self.missed_sms_count >= 2:
                self.status = 'missed'
            self.save()

        return self.participant.send_automated_message(send=send,send_base='visit',condition=condition)

    def get_condition(self,postfix='pre'):
        if self.is_pregnant():
            prefix = 'anc'
        elif self.visit_type == 'both':
            prefix = 'both'
        else:
            prefix = 'pnc'
        return '{}_{}'.format(prefix,postfix)

    def is_pregnant(self):
        return self.participant.was_pregnant(self.scheduled)

    @property
    def no_sms(self):
        return self.status in Visit.NO_SMS_STATUS

class ScheduledPhoneCallQuerySet(SchedualQuerySet):

    def pending_calls(self):
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
