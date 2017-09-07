from django.db import models
from contacts.models.contact import ContactBase


class ExampleContact(ContactBase):
    """
    Sample Implementation of the Contact model, demonstrating simple inheritance.

    To use this model, add the following line to settings:

    CONTACTS_CONTACT_MODEL = 'example.ExampleContact'
    """
    a_new_field = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        app_label = 'example'
