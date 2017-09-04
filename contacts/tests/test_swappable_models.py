from django import test
from django.test import override_settings, modify_settings
from contacts import get_contact_model
from implementations.example.models import ExampleContact


@override_settings(CONTACTS_CONTACT_MODEL='example.ExampleContact')
@modify_settings(INSTALLED_APPS={
    'append': 'implementations.example'
})
class SwappableModelTest(test.TestCase):

    def test_swappable_model_accessor(self):
        self.assertEqual(ExampleContact, get_contact_model())
