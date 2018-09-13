import datetime

from django import test
from django.conf import settings
from django.db import models
from django.test import override_settings
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

        # self.assertFalse(self.p3.is_active)

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

        self.assertEqual( participants.count() , 5 )

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

    def test_send_auto(self):

        p1_count = self.p1.message_set.count()
        new_message = self.p1.send_automated_message()

        self.assertEqual(new_message.text,self.auto_1_message.english.format(name=self.p1.nickname.title()))
        self.assertEqual(self.p1.message_set.count(),p1_count+1)
        self.assertEqual(new_message.external_id,"Default Transport")
        self.assertEqual(new_message.external_status,"Sent")

        p2_count = self.p2.message_set.count()
        new_message = self.p2.send_automated_message()

        self.assertEqual(new_message.text,self.auto_2_message.luo.format(name=self.p2.nickname.title()))
        self.assertEqual(self.p2.message_set.count(),p2_count+1)
        self.assertEqual(new_message.external_id,"Default Transport")
        self.assertEqual(new_message.external_status,"Sent")

        p3_count = self.p3.message_set.count()
        new_message = self.p3.send_automated_message()

        self.assertEqual(new_message.text,self.auto_3_message.english.format(name=self.p3.nickname.title()))
        self.assertEqual(self.p3.message_set.count(),p3_count+1)
        self.assertEqual(new_message.external_id,"Default Transport")
        self.assertEqual(new_message.external_status,"Sent")

        p4_count = self.p4.message_set.count()
        new_message = self.p4.send_automated_message()

        print self.p4.description()

        self.assertEqual(new_message.text,self.auto_4_message.english.format(name=self.p4.nickname.title()))
        self.assertEqual(self.p4.message_set.count(),p4_count+1)
        self.assertEqual(new_message.external_id,"Default Transport")
        self.assertEqual(new_message.external_status,"Sent")

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
        self.assertEqual(len(response.data), 4)

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
