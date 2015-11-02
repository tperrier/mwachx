from django.db import models

class Facility(models.Model):

    class Meta:
        verbose_name_plural = 'facilities'
        app_label = 'backend'

    name = models.CharField(max_length='50',help_text='Facility Name')

    def __str__(self):
        # Change snake_case to Snake Case
        return self.name.replace('_',' ').title()

# TODO: Add Automated Message Model

class AutomatedMessage(models.Model):
    """Automated Messages for sending to participants"""

    class Meta:
        app_label = 'backend'

    OFFSET_UNITS = (
        ('d','Days'),
        ('w','Weeks'),
    )

    priority = models.IntegerField(default=0)

    message = models.TextField()
    comment = models.TextField(blank=True)
    tags = models.ManyToManyField("MessageTag")

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
    type = models.CharField(max_length=15,default='other')

    def __unicode__(self):
        return self.display.title() if self.display else self.name.title()
