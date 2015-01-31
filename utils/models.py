from django.db import models
from django.core.exceptions import ObjectDoesNotExist
# Create your models here.

class TimeStampedModel(models.Model):

    class Meta:
        ordering = ('-created',)
    
    #The date and time this message was created or modified
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def created_str(self,format='%Y-%m-%d %H:%M'):
        return self.created.strftime(format)

    class Meta:
        abstract = True
        
class BaseQuerySet(models.QuerySet):
    
    def get_or_none(self,**kwargs):
        return self.get_or_default(None,**kwargs)
            
    def get_or_default(self,default=None,**kwargs):
        try:
            return self.get(**kwargs)
        except ObjectDoesNotExist:
            return default
