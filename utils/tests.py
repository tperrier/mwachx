from django.test import TestCase
import sms_utils as sms

class UtilsTestCase(TestCase):

    def test_clean_msg(self):

        msgs = ['Hello. World','Hello.  World','Hello?     World    ','Hello      World.  ']
        cleaned = ['Hello. World','Hello. World','Hello? World','Hello World.']
        for msg , clean in zip(msgs,cleaned):
            self.assertEqual( sms.clean_msg(msg) , clean )
