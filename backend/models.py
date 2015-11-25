from django.db import models

import utils.models as utils

class AutomatedMessageQuerySet(utils.BaseQuerySet):

    def for_participant(self,participant,send_base=None,send_offset=0):
        if send_base is None:
            send_base = 'edd' if participant.is_pregnant() else 'dd'
            send_offset = participant.delta_days()/7

        message_set = self.filter(send_base=send_base, send_offset=send_offset,
            hiv_messaging=participant.hiv_messaging == 'system')

        # TODO: selecting the first might not be the best stratagy
        message = message_set.filter(condition=participant.condition, group=participant.study_group).first()

        if message is None: # No match for participant conditions
            # Try to grab the normal message
            message = message_set.filter(condition='normal', group=participant.study_group).first()

        if message is None:
            # If message is is still none don't check group
            message = message_set.filter(condition='normal').first()

        return message

    def from_description(self,description):
        send_base, group, condition, hiv, send_offset = description.split('.')
        hiv = hiv == 'Y'
        send_offset = int(send_offset)
        return self.get_or_none(send_base=send_base, send_offset=send_offset, group=group, condition=condition,
            hiv_messaging=hiv)

    def from_excel(self,msg):
        auto = self.from_description(msg.description())
        if auto is None:
            return self.create(**msg.kwargs())
        else:
            auto.english = msg.english
            auto.swahili = msg.swahili
            auto.luo = msg.luo
            auto.save()
            return auto

class AutomatedMessage(models.Model):
    """Automated Messages for sending to participants"""

    SEND_BASES_CHOICES = (
        ('edd','Before EDD'),
        ('over','Post Dates'),
        ('post','Postpartum'),
        ('visit','Visit Messages'),
        ('signup','From Signup'),
        ('connect','Reconnect Messages'),
    )

    GROUP_CHOICES = (
        ('control','Control'),
        ('one-way','One Way'),
        ('two-way','Two Way'),
    )

    CONDITION_CHOICES = (
        ('art','Starting ART'),
        ('adolescent','Adolescent'),
        ('first','First Time Mother'),
        ('normal','Normal'),
    )

    class Meta:
        app_label = 'backend'

    objects = AutomatedMessageQuerySet.as_manager()

    priority = models.IntegerField(default=0)

    english = models.TextField(blank=True)
    swahili = models.TextField(blank=True)
    luo = models.TextField(blank=True)

    comment = models.TextField(blank=True)

    group = models.CharField(max_length=10,choices=GROUP_CHOICES) # 2 groups
    condition = models.CharField(max_length=10,choices=CONDITION_CHOICES) # 4 conditions
    hiv_messaging = models.BooleanField() # True or False

    send_base = models.CharField(max_length=10,help_text='Base to send messages from',choices=SEND_BASES_CHOICES)
    send_offset = models.IntegerField(default=0,help_text='Offset from base in weeks')

    todo = models.BooleanField()

    def category(self):
        return "{0.send_base}.{0.group}.{0.condition}.{1}".format(self,
            'Y' if self.hiv_messaging else 'N')

    def description(self):
        return "{0}.{1}".format(self.category(),self.send_offset)

    def get_language(self,language):
        # TODO: Error checking
        return getattr(self,language)
