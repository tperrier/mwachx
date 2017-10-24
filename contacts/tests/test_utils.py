import datetime

from django.contrib.auth import models as auth

import contacts.models as cont
import backend.models as auto

def setup_auth_user(cls):
    # Creat dummy admin user
    cls.user = auth.User.objects.create_user("test", "t@t.com", "test",first_name="Test Nurse")
    cont.Practitioner.objects.create(user=cls.user, facility="bondo")

def setup_auto_messages(cls):
    # Create dummy auto messages
    cls.signup_control_msg = auto.AutomatedMessage.objects.create(
        send_base="signup",
        english="Control English Signup Message",
        hiv_messaging=False,
        todo=False,
        group='control',
        condition='normal',
    )

    cls.signup_msg = auto.AutomatedMessage.objects.create(
        send_base="signup",
        english="English Signup Message",
        hiv_messaging=False,
        todo=False,
        group='two-way',
        condition='normal',
    )

    cls.auto_edd_message = auto.AutomatedMessage.objects.create(
        send_base="edd",
        send_offset=3,
        english="Hi {name} auto.edd",
        hiv_messaging=False,
        todo=False,
        condition='normal',
        group='two-way',
    )

    cls.auto_dd_message = auto.AutomatedMessage.objects.create(
        send_base="dd",
        send_offset=3,
        english="Hi {name} auto.dd (English)",
        luo="Hi {name} auto.dd (Luo)",
        hiv_messaging=False,
        todo=False,
        condition='art',
        group='two-way',
    )

    cls.auto_second_message = auto.AutomatedMessage.objects.create(
        send_base="dd",
        send_offset=4,
        english="Hi {name} auto.second",
        hiv_messaging=False,
        todo=False,
        condition='preg2',
        group='two-way',
    )

def setup_basic_contacts(cls):
    # Create basic contact objects

    #pregnant contact three weeks until EDD
    cls.p1 = cont.Contact.objects.create(
        study_id="0001",
        anc_num="0001",
        facility="bondo",
        study_group="two-way",
        nickname="p1 one",
        birthdate=datetime.date(1986, 8, 5),
        due_date=datetime.date.today() + datetime.timedelta(weeks=3),
    )

    cls.p1_connection = cont.Connection.objects.create(
        identity="P1 Connection",
        contact=cls.p1,
        is_primary=True
    )

    #post-partum contact three weeks since delivery
    cls.p2 = cont.Contact.objects.create(
        study_id="0002",
        anc_num="0002",
        facility="bondo",
        study_group="two-way",
        nickname="p2",
        birthdate=datetime.date(1986, 8, 5),
        due_date=datetime.date.today() - datetime.timedelta(weeks=3),
        delivery_date=datetime.date.today() - datetime.timedelta(weeks=3),
        status="post",
        hiv_messaging="system",
        language='luo',
        condition='art',
    )

    cls.p2_connection = cont.Connection.objects.create(
        identity="P2 Connection",
        contact=cls.p2,
        is_primary=True
    )

    # control contact
    cls.p3 = cont.Contact.objects.create(
        study_id="0003",
        anc_num="0003",
        facility="ahero",
        study_group="control",
        nickname="p3",
        birthdate=datetime.date(1986, 8, 5),
        due_date=datetime.date.today() - datetime.timedelta(weeks=6),
        status="stopped",
        delivery_date=datetime.date.today() - datetime.timedelta(weeks=3),
        condition='art',
    )

    cls.p3_connection = cont.Connection.objects.create(
        identity="P3 Connection",
        contact=cls.p3,
        is_primary=True
    )

    #second pregnancy contact
    cls.p4 = cont.Contact.objects.create(
        study_id="0004",
        anc_num="0004",
        facility="ahero",
        study_group="two-way",
        nickname="p4",
        birthdate=datetime.date(1986, 8, 5),
        due_date=datetime.date.today() - datetime.timedelta(weeks=6),
        delivery_date=datetime.date.today() - datetime.timedelta(weeks=3),
        status="post",
        condition="art",
        second_preg=True,
    )

    cls.p4_connection = cont.Connection.objects.create(
        identity="P4 Connection",
        contact=cls.p4,
        is_primary=True
    )
