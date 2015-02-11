#!/usr/bin/python
# Django Imports
from django.db import models
from django.conf import settings

# Local Imports
from utils.models import TimeStampedModel

class Translation(TimeStampedModel):
	parent = models.ForeignKey('contacts.Message',related_name='original_message')
	text = models.CharField(max_length=1000,help_text='Text of the translated message')

	is_complete= models.BooleanField(default=False)