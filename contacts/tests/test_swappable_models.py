from django import test
from django.conf import settings
from django.test import override_settings, modify_settings
from django.utils import unittest
from contacts import get_contact_model
from contacts.tests import test_utils
from implementations.example.models import ExampleContact


@override_settings(CONTACTS_CONTACT_MODEL='example.ExampleContact')
@modify_settings(INSTALLED_APPS={
    'append': 'implementations.example'
})
class SwappableModelTest(test.TestCase):

    def test_swappable_model_accessor(self):
        self.assertEqual(ExampleContact, get_contact_model())

    @unittest.skipUnless(settings.TEST_CONTACT_SWAPPING, "requires swapped models")
    def test_db_access(self):
        # todo: this currently fails because the override of the swappable model
        # happens after the DB is initialized.
        # there may be some complex workarounds to this (https://stackoverflow.com/q/502916/8207),
        # but for now just take the same approach that the framework does
        # (see: https://github.com/wq/django-swappable-models/blob/master/tests/test_swapper.py#L61)
        self.assertEqual(0, get_contact_model().objects.count())

    @unittest.skipUnless(settings.TEST_CONTACT_SWAPPING, "requires swapped models")
    def test_save_load(self):
        test_utils.setup_basic_contacts(self)
        self.assertEqual(3, get_contact_model().objects.count())
        self.p1.a_new_field = 'test the new stuff'
        self.p1.save()
        self.assertEqual('test the new stuff', get_contact_model().objects.get(pk=self.p1.pk).a_new_field)
