
#!/usr/bin/python
#Django Imports
from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from jsonfield import JSONField

#Local Imports
from utils.models import TimeStampedModel,BaseQuerySet

class ForwardMessage(TimeStampedModel):
    """
    A ForwardMessage is a message *instance* for incoming messages forwarded
    to a different instance of mWACH
    """

    STATUS_CHOICES = (
        ('success','Success'),
        ('failed','Failed'),
        ('none','No Forward In Transport')
    )

    #Set Custom Manager
    objects = BaseQuerySet.as_manager()

    class Meta:
        ordering = ('-created',)
        app_label = 'transports'

    identity = models.CharField(max_length=25)
    text = models.TextField(help_text='Text of the SMS message')
    transport = models.CharField(max_length=25,help_text='Transport name')
    fwrd_status = models.CharField(max_length=25,choices=STATUS_CHOICES,help_text='Forward Status')
    url = models.CharField(max_length=250,help_text='Forward URL')

    #Africa's Talking Data Only for outgoing messages
    external_id = models.CharField(max_length=50,blank=True)
    external_data = JSONField(blank=True)
