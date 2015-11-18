from django.db import models

class Facility(models.Model):

    class Meta:
        verbose_name_plural = 'facilities'
        app_label = 'backend'

    name = models.CharField(max_length='50',help_text='Facility Name')

    def __str__(self):
        # Change snake_case to Snake Case
        return self.name.replace('_',' ').title()

class AutomatedMessageQuerySet(models.QuerySet):

    def filter_participant(self,participant,send_base=None,send_offset=0):
        if send_base is None:
            send_base = 'edd' if participant.is_pregnant() else 'dd'
            send_offset = participant.delta_days()/7

        message_set = self.filter(send_base=send_base, send_offset=send_offset, group=participant.study_group,
            language=participant.language,hiv_messaginig=participant.hiv_messaging == 'system')
        # TODO: selecting the first might not be the best stratagy
        message = message_set.filter(condition=participant.condition).first()

        if message is None: # No match for participant conditions
            # Try to grab the normal message
            message = message_set.filter(condition='normal').first()

        return message

    def from_description(self,description):
        send_base, send_offset, group, condition, hiv, language = description.split('_')
        hiv = hiv == 'Y'
        return self.get(send_base=send_base, send_offset=send_offset, group=group, condition=condition,
            hiv_messaging=hiv,language=language)


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

    LANGUAGE_CHOICES = (
        ('english','English'),
        ('luo','Luo'),
        ('swahili','Swahili'),
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

    message = models.TextField()
    comment = models.TextField(blank=True)

    group = models.CharField(max_length=10,choices=GROUP_CHOICES) # 2 groups
    condition = models.CharField(max_length=10,choices=CONDITION_CHOICES) # 4 conditions
    hiv_messaging = models.BooleanField() # True or False
    language = models.CharField(max_length=10,choices=LANGUAGE_CHOICES) # 3 languages

    send_base = models.CharField(max_length=10,help_text='Base to send messages from',choices=SEND_BASES_CHOICES)
    send_offset = models.IntegerField(default=0,help_text='Offset from base in weeks')

    def category(self):
        return "{0.send_base}_{0.group}_{0.condition}_{1}_{0.language}".format(self,
            'Y' if self.hiv_messaging else 'N')

    def description(self):
        return "{0}_{1}".format(self.category,self.send_offset)
