import datetime

from django.contrib.auth import models as auth
from contacts import get_contact_model

import contacts.models as cont
import backend.models as auto

Contact = get_contact_model()

def setup_auth_user(cls):
    # Creat dummy admin user
    cls.user = auth.User.objects.create_user("test", "t@t.com", "test",first_name="Test Nurse")
    cont.Practitioner.objects.create(user=cls.user, facility="migosi")

def setup_auto_messages(cls):
    # Create dummy auto messages

    cls.signup_msg = auto.AutomatedMessage.objects.create(
        send_base="signup",
        english="English Signup Message",
        todo=False,
        condition='normal',
    )

    cls.auto_edd_message = auto.AutomatedMessage.objects.create(
        send_base="edd",
        send_offset=3,
        english="Hi {name} Hi",
        todo=False
    )

    cls.auto_dd_message = auto.AutomatedMessage.objects.create(
        send_base="fp",
        send_offset=2,
        english="DD {name} DD",
        todo=False
    )

def setup_basic_contacts(cls):
    # Create basic contact objects
    cls.p1 = Contact.objects.create(
        study_id="0001",
        facility="migosi",
        nickname="p1 one",
        birthdate=datetime.date(1986, 8, 5),
        due_date=datetime.date.today() + datetime.timedelta(weeks=3),
        prep_initiation=datetime.date.today() - datetime.timedelta(weeks=1),
        condition="preg",
    )

    cls.p1_connection = cont.Connection.objects.create(
        identity="P1 Connection",
        contact=cls.p1,
        is_primary=True
    )

    cls.p2 = Contact.objects.create(
        study_id="0002",
        anc_num="0002",
        facility="kisumu",
        language='luo',
        nickname="p2",
        birthdate=datetime.date(1986, 8, 5),
        due_date=datetime.date.today() - datetime.timedelta(weeks=3),
        delivery_date=datetime.date.today() - datetime.timedelta(weeks=3),
        prep_initiation=datetime.date.today() - datetime.timedelta(weeks=2),
        condition="post",
    )

    cls.p2_connection = cont.Connection.objects.create(
        identity="P2 Connection",
        contact=cls.p2,
        is_primary=True
    )

    cls.p3 = Contact.objects.create(
        study_id="0003",
        anc_num="0003",
        facility="migosi",
        nickname="p3",
        birthdate=datetime.date(1986, 8, 5),
        due_date=datetime.date.today() - datetime.timedelta(weeks=6),
        status="stopped",
        delivery_date=datetime.date.today() - datetime.timedelta(weeks=3),
        prep_initiation=datetime.date.today() - datetime.timedelta(weeks=3),
        condition="famp",
    )

    cls.p3_connection = cont.Connection.objects.create(
        identity="P3 Connection",
        contact=cls.p3,
    )
