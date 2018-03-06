import datetime

from django import test
from django.conf import settings
from django.db import models
from django.test import override_settings
from django.utils import unittest
from rest_framework import test as rf_test
import django.core.urlresolvers as url
from django.core import management
from contacts import get_contact_model

import test_utils

Contact = get_contact_model()


class SystemCheckTest(test.TestCase):

    def test_check(self):
        management.call_command('check')

class ParticipantBasicTests(test.TestCase):

    @classmethod
    def setUpTestData(cls):
        test_utils.setup_auth_user(cls)
        test_utils.setup_basic_contacts(cls)
        test_utils.setup_auto_messages(cls)

    def setUp(self):
        self.p1.refresh_from_db()

    def test_str(self):
        # test Participant string output
        self.assertEqual(str(self.p1), "P1 One")
        self.assertEqual(str(self.p2), "P2")

    def test_connection(self):
        # test Participant connection
        self.assertEqual(self.p1.connection(), self.p1_connection)
        self.assertEqual(self.p2.connection(), self.p2_connection)

    def test_phonenumber(self):
        # test Participant phone number
        self.assertEqual(self.p1.phone_number(), self.p1_connection.identity)
        self.assertEqual(self.p2.phone_number(), self.p2_connection.identity)

    def test_active(self):
        self.assertTrue(self.p1.is_active)
        self.assertFalse(self.p1.no_sms)
        self.assertFalse(self.p3.is_active)
        self.assertTrue(self.p3.no_sms)

    @override_settings(FAKE_DATE=False)
    def test_description(self):
        self.assertEqual(self.p1.description(), "prep.preg.7")
        self.assertEqual(self.p2.description(), "prep.post.14")
        self.assertEqual(self.p3.description(send_base='signup', send_offset=0), "signup.famp.0")

        # Test FP Methods
        def plus_td(weeks=0,days=0):
            return datetime.date.today() + datetime.timedelta(days=days,weeks=weeks)

        self.assertEqual(self.p2.description(today=plus_td(days=2)), "prep.post.14")
        self.assertEqual(self.p2.description(today=plus_td(days=8)), "prep.post.21")
        self.assertEqual(self.p2.description(today=plus_td(2)), "prep.post.28")
        self.assertEqual(self.p2.description(today=plus_td(3)), "prep.post.35")
        self.assertEqual(self.p2.description(today=plus_td(7)), "prep.post.63")

    def test_send_batch(self):

        participants = Contact.objects.annotate(msg_count=models.Count('message'))
        self.assertEqual( participants.count() , 3 )

        before_count = sum( p.msg_count for p in participants )

        # Test Send = False
        participants.send_batch('English Message','Swahili Message','Luo Message',
            auto='test',send=False)
        participants = participants.filter() # reload participants from db
        after_count = sum( p.msg_count for p in participants )
        self.assertEqual( before_count , after_count )

        # Test send = true
        participants.send_batch('English Message','Swahili Message','Luo Message',
            auto='test',send=True)
        participants = participants.filter() # reload participants from db
        after_count = sum( p.msg_count for p in participants )
        self.assertEqual( before_count + len(participants) - 1 , after_count )

        new_message = self.p2.message_set.first()
        self.assertEqual( new_message.auto , 'custom.test' )
        self.assertEqual( new_message.translation_status , 'cust' )
        self.assertEqual( new_message.text , 'Luo Message' )
        self.assertEqual( new_message.translated_text, 'English Message' )
        self.assertTrue( new_message.is_outgoing )
        self.assertFalse( new_message.is_system )
        self.assertEqual( new_message.contact , self.p2 )

        # Test send = true no auto tag
        participants.send_batch('English Message','Swahili Message','Luo Message',send=True)
        new_message = self.p2.message_set.first()
        self.assertEqual( new_message.auto , 'custom' )
        self.assertEqual( new_message.translation_status , 'cust' )

class ParticipantSerializerTests(rf_test.APITestCase):

    @classmethod
    def setUpTestData(cls):
        test_utils.setup_auth_user(cls)
        test_utils.setup_basic_contacts(cls)
        test_utils.setup_auto_messages(cls)

    def setUp(self):
        self.client.login(username="test", password="test")

    def test_participant_list(self):
        response = self.client.get(url.reverse('participant-list'))
        self.assertEqual(len(response.data), 2)

    def test_participant_detail(self):
        response = self.client.get(url.reverse('participant-detail',args=['0001']))
        self.assertEqual(response.data['nickname'],'P1 one')
        self.assertEqual(response.data['study_id'],'0001')

    def test_pending(self):
        # Check pending home page countso

        # Send a message to P1 so there is some data
        import transports
        transports.receive("P1 Connection", "Message Content")

        response = self.client.get(url.reverse("pending-list"))
        self.assertEqual(len(response.data), 8)
        self.assertEqual(response.data["messages"], 1)
        self.assertEqual(response.data["translations"], 1)

        response = self.client.get(url.reverse("pending-messages"))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['text'], "Message Content")

    @unittest.skipUnless(not settings.TEST_CONTACT_SWAPPING, "not compatible with swapped models")
    def test_create(self):

        start_count = Contact.objects.count()
        data = { "previous_pregnancies":0,"study_id":"0004","anc_num":"0004","study_group":"two-way",
                 "language":"english","phone_number":"0700000004","nickname":"Test","birthdate":"1990-02-05",
                 "relationship_status":"single","due_date":"2016-07-29","condition":"preg",
                 "clinic_visit":"2016-07-22","send_day":'',"send_time":20, "prep_initiation":"2016-06-15"}
        response = self.client.post(url.reverse("participant-list"), data, format="json")
        # import code;code.interact(local=locals())

        try:
            new_participant = Contact.objects.get(study_id="0004")
        except Contact.DoesNotExist as e:
            self.fail( response )

        # Check that the participant was created
        self.assertEqual(Contact.objects.count(),start_count+1)
        self.assertEqual(new_participant.nickname,'Test')
        self.assertEqual(new_participant.facility,self.user.practitioner.facility)
        self.assertEqual(new_participant.phone_number(),"+254700000004")
        self.assertEqual(new_participant.send_time,20)
        self.assertEqual(new_participant.send_day,1)

        # Check that the welcome message was sent
        self.assertEqual(new_participant.message_set.count(),1)
        self.assertEqual(new_participant.message_set.first().text,self.signup_msg.english)
        self.assertEqual(new_participant.message_set.first().auto,self.signup_msg.description())
