from django.db import models

class Facility(models.Model):

    class Meta:
        verbose_name_plural = 'facilities'
        app_label = 'backend'

    name = models.CharField(max_length='50',help_text='Facility Name')

    def __str__(self):
        # Change snake_case to Snake Case
        return ' '.join([word.capitalize() for word in self.name.split('_')])

# TODO: Add EventLogger Model


# TODO: Add Automated Message Model
