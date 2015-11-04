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

    def filter_tags(self,tags='normal'):
        if isinstance(tags,basestring):
            tags = [tags]
        #else assume conditions is a list of strings
        return self.filter(tags__name__in=tags)

    def filter_offset(self,send_base,send_offset):
        ''' Find any messages for today or the last six days '''
        days_range = (send_offset - 6, send_offset)
        return self.filter(send_base__name=send_base,send_offset__range=days_range)

    def filter_participant(self,participant,send_base=None,send_offset=0):
        if send_base is None:
            send_base = 'edd' if participant.is_pregnant() else 'dd'
            send_offset = participant.get_offset()

        tags = [participant.language,participant.condition]

        message_set = self.filter_offset(send_base,send_offset)
        message = message_set.filter_tags().first() # TODO: selecting the first might not be the best stratagy

        if message is None: # No match for participant conditions
            # Try to grab the normal message
            tags.append('normal')
            message = message_set.filter_tags(tags).first()

        if message is None:
            # If still none try looking for the english version
            tags.append('english')
            message = message_set.filter_tags(tags).first()

        return message


class AutomatedMessage(models.Model):
    """Automated Messages for sending to participants"""

    class Meta:
        app_label = 'backend'

    OFFSET_UNITS = (
        ('d','Days'),
        ('w','Weeks'),
    )

    objects = AutomatedMessageQuerySet.as_manager()

    priority = models.IntegerField(default=0)

    message = models.TextField()
    comment = models.TextField(blank=True)
    tags = models.ManyToManyField("MessageTag",limit_choices_to= ~models.Q(type='base'))

    send_base = models.ForeignKey("MessageTag",related_name='base_set',limit_choices_to={'type':'base'})
    send_offset = models.IntegerField(default=0)
    send_offset_unit = models.CharField(max_length=1,choices=OFFSET_UNITS,default='w')

    def for_participant(self,participant):
        return self.message

class MessageTag(models.Model):

    class Meta:
        app_label = 'backend'

    TAG_TYPES = (
        ('base','Send Base'),
        ('language','Language'),
        ('group','Study Group'),
        ('condition','Condition'),
        ('other','Other'),
    )

    name = models.CharField(max_length=30)
    display = models.CharField(max_length=100, blank=True)
    type = models.CharField(max_length=15,choices=TAG_TYPES,default='other')

    def __unicode__(self):
        return self.display.title() if self.display else self.name.title()
