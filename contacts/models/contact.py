#!/usr/bin/python
# Python Imports
from hashlib import sha256
import collections
import datetime, numbers

# Django Imports
from django.conf import settings
from django.db import models

# Local Imports
from contacts.models import PhoneCall, Practitioner, Visit, Connection
from utils import enums
from utils.models import TimeStampedModel, ForUserQuerySet
import backend.models as back
import utils
import transports


class ContactQuerySet(ForUserQuerySet):

    participant_field = None

    def get_from_phone_number(self,phone_number):
        try:
            return Connection.objects.get(identity=phone_number).contact
        except Connection.DoesNotExist as e:
            raise Contact.DoesNotExist()

    def annotate_messages(self):

        return self.annotate(
            msg_outgoing=utils.sql_count_when(message__is_outgoing=True),
            msg_system=utils.sql_count_when(message__is_system=True),
            msg_nurse=utils.sql_count_when(~models.Q(message__translation_status='cust'),
            message__is_system=False,message__is_outgoing=True),
            msg_incoming=utils.sql_count_when(message__is_outgoing=False),
            msg_delivered=utils.sql_count_when(message__external_status='Success'),
            msg_sent=utils.sql_count_when(message__external_status='Sent'),
            msg_failed=utils.sql_count_when(message__external_status='Failed'),
        ).annotate(
            msg_missed=models.F('msg_outgoing') - models.F('msg_delivered'),
            msg_other=models.F('msg_outgoing') - models.F('msg_delivered') - models.F('msg_sent'),
            # sim_count=models.Count('connection',distinct=True),
        )

    def send_batch(self,english,swahili=None,luo=None,auto='',send=False,control=False):
        """ Send a message to all participants in the query set
            english: required text
            swahili, luo: optional translated text
            auto: string to tag in the auto link field, will prefix with custom.
            send: boolean flag to send messages (default false)
            control: boolean flag to send messages to control group (default false)
        """

        if swahili is None:
            swahili = english
        if luo is None:
            luo = english
        text_translations = {'english':english,'swahili':swahili,'luo':luo}

        original_count = self.count()
        send_to = self.active_users()
        send_count = send_to.count()
        print "Sending to {} of {}".format(send_count,original_count)

        counts = collections.Counter()
        for p in send_to.all():
            # Send the correct language message to all participants
            text = text_translations.get(p.language,english)
            text = text.format( **p.message_kwargs() )

            if send is True:
                msg = p.send_message(
                    text=text,
                    translation_status='cust',
                    auto='custom.{}'.format(auto) if auto != '' else 'custom',
                    translated_text= english if p.language != english else '',
                    control=control,
                    is_system=False,
                )
                counts[msg.external_status] += 1
            else:
                print "({}) -- {}".format(p , text[:40])

        if send is True:
            print "Send Status:\n", "\n\t".join( "{} -> {}".format(key,count) for key,count in counts.most_common() )

        return send_count


class ContactManager(models.Manager):

    def get_queryset(self):
        qs = super(ContactManager,self).get_queryset()
        return qs.annotate(
            note_count=models.Count('note',distinct=True),
            phonecall_count=models.Count('phonecall',distinct=True),
        ).prefetch_related('connection_set',
            models.Prefetch(
                'visit_set',
                queryset=Visit.objects.order_by('scheduled').filter(arrived__isnull=True,status='pending'),
                to_attr='pending_visits'
            )
        )


class Contact(TimeStampedModel):

    STATUS_CHOICES = (
        ('pregnant','Pregnant'),
        ('over','Post-Date'),
        ('post','Post-Partum'),
        ('ccc','CCC'),
        ('completed','Completed'),
        ('stopped','Withdrew'),
        ('loss','SAE opt-in'),
        ('sae','SAE opt-out'),
        ('other','Admin Stop'),
        ('quit','Left Study'),
    )

    NO_SMS_STATUS = ForUserQuerySet.NO_SMS_STATUS
    NOT_ACTIVE_STATUS = ForUserQuerySet.NOT_ACTIVE_STATUS

    LANGUAGE_CHOICES = (
        ('english','English'),
        ('luo','Luo'),
        ('swahili','Swahili'),
    )

    CONDITION_CHOICES = (
        ('art','1 - Starting ART'),
        ('adolescent','2 - Adolescent'),
        ('first','3 - First Time Mother'),
        ('normal','4 -  Normal'),
        ('multiple','5 - Twins'),
    )

    FAMILY_PLANNING_CHOICES = (
        ('none','None'),
        ('iud','IUD'),
        ('pill','Pills'),
        ('depot','Depot'),
        ('implant','Implant'),

    )

    RELATIONSHIP_CHOICES = (
        ('single','Single'),
        ('partner','Partner'),
        ('married','Married'),
        ('seperated','Seperated'),
    )

    DAY_CHOICES = (
        (0,'Monday'),
        (1,'Tuesday'),
        (2,'Wednesday'),
        (3,'Thursday'),
        (4,'Friday'),
        (5,'Satuday'),
        (6,'Sunday'),
    )

    TIME_CHOICES = (
        (8,'Morning (8 AM)'),
        (13,'Afternoon (1 PM)'),
        (20,'Evening (8 PM)'),
    )

    MESSAGING_CHOICES = (
        ('none','No HIV Messaging'),
        ('initiated','HIV Content If Initiated'),
        ('system','HIV Content Allowed'),
    )

    DELIVERY_SOURCE_CHOICES = (
        ('phone','Phone'),
        ('sms','SMS'),
        ('visit','Clinic Visit'),
        ('m2m',"Mothers to Mothers"),
        ('other','Other'),
    )

    #Set Custom Manager
    objects = ContactManager.from_queryset(ContactQuerySet)()
    objects_no_link = ContactQuerySet.as_manager()

    #Study Attributes
    study_id = models.CharField(max_length=10,unique=True,verbose_name='Study ID',help_text="* Use Barcode Scanner")
    anc_num = models.CharField(max_length=15,verbose_name='ANC #')
    ccc_num = models.CharField(max_length=15,verbose_name='CCC #',blank=True,null=True)
    facility = models.CharField(max_length=15,choices=settings.FACILITY_CHOICES)

    study_group = models.CharField(max_length=10,choices=enums.GROUP_CHOICES,verbose_name='Group')
    send_day = models.IntegerField(choices=DAY_CHOICES, default=0,verbose_name='Send Day')
    send_time = models.IntegerField(choices=TIME_CHOICES,default=8,verbose_name='Send Time')

    # Required Client Personal Information
    nickname = models.CharField(max_length=20)
    birthdate = models.DateField(verbose_name='DOB')

    # Optional Clinet Personal Informaiton
    partner_name = models.CharField(max_length=40,blank=True,verbose_name='Partner Name')
    relationship_status = models.CharField(max_length=15,choices=RELATIONSHIP_CHOICES,verbose_name='Relationship Status',blank=True)
    previous_pregnancies = models.IntegerField(blank=True,null=True,help_text='* excluding current')
    phone_shared = models.NullBooleanField(verbose_name='Phone Shared')

    # Required Medical Information
    status = models.CharField(max_length=15,choices=STATUS_CHOICES, default='pregnant')
    language = models.CharField(max_length=10,choices=LANGUAGE_CHOICES,default='english')
    condition = models.CharField(max_length=15,choices=CONDITION_CHOICES,default='normal')
    due_date = models.DateField(verbose_name='Estimated Delivery Date')

    delivery_date = models.DateField(verbose_name='Delivery Date',blank=True,null=True)
    delivery_source = models.CharField(max_length=10,verbose_name="Delivery Notification Source",choices=DELIVERY_SOURCE_CHOICES,blank=True)

    # Optional Medical Informaton
    art_initiation = models.DateField(blank=True,null=True,help_text='Date of ART Initiation',verbose_name='ART Initiation')
    hiv_disclosed = models.NullBooleanField(blank=True,verbose_name='HIV Disclosed')
    hiv_messaging = models.CharField(max_length=15,choices=MESSAGING_CHOICES,default='none',verbose_name='HIV Messaging')
    child_hiv_status = models.NullBooleanField(blank=True,verbose_name='Child HIV Status')
    family_planning = models.CharField(max_length=10,blank=True,choices=FAMILY_PLANNING_CHOICES,verbose_name='Family Planning')
    loss_date = models.DateField(blank=True,null=True,help_text='SAE date if applicable')
    second_preg = models.BooleanField(blank=True,choices=enums.BOOL_CHOICES,verbose_name='Second Pregnancy',default=False)

    #State attributes to be edited by the system
    last_msg_client = models.DateField(blank=True,null=True,help_text='Date of last client message received',editable=False)
    last_msg_system = models.DateField(blank=True,null=True,help_text='Date of last system message sent',editable=False)
    is_validated = models.BooleanField(default=False,blank=True)
    validation_key = models.CharField(max_length=5,blank=True)

    class Meta:
        app_label = 'contacts'

    def __init__(self, *args, **kwargs):
        ''' Override __init__ to save old status'''
        super(Contact,self).__init__(*args,**kwargs)
        self._old_status = self.status
        self._old_hiv_messaging = self.hiv_messaging

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        # Check that self.id exists so this is not the first save
        if not self._old_status == self.status and self.id is not None:
            self.statuschange_set.create(old=self._old_status,new=self.status,comment='Status Admin Change')

        if not self._old_hiv_messaging == self.hiv_messaging and self.id is not None:
            print self._old_hiv_messaging, self.hiv_messaging
            self.statuschange_set.create(old=self._old_hiv_messaging,new=self.hiv_messaging,
                comment='HIV messaging changed',type='hiv')

        # Force capitalization of nickname
        self.nickname = self.nickname.capitalize()

        super(Contact,self).save(force_insert,force_update,*args,**kwargs)
        self._old_status = self.status
        self._old_hiv_messaging = self.hiv_messaging

    def __str__ (self):
        return self.nickname.title()

    def __repr__(self):
        return "(#%03s) %s (%s)"%(self.study_id,self.nickname.title(),self.facility.title())

    def connection(self):
        # Use connection_set.all() instead of .filter to take advantage of prefetch_related
        for connection in self.connection_set.all():
            if connection.is_primary == True:
                return connection

    def phone_number(self):
        connection = self.connection()
        if connection is not None:
            return connection.identity

    @property
    def is_active(self):
        # True if contact is receiving SMS messages
        return self.status not in Contact.NOT_ACTIVE_STATUS

    @property
    def no_sms(self):
        return self.status in Contact.NO_SMS_STATUS

    def age(self,signup=False):
        if signup is True:
            today = self.created.date()
        else:
            today = utils.today()
        if today < datetime.date(today.year,self.birthdate.month,self.birthdate.day):
            return today.year - self.birthdate.year - 1
        else:
            return today.year - self.birthdate.year

    def age_signup(self):
        return self.age(True)

    def next_visit(self):
        ''' Return The Next Visit'''
        pending = self.visit_set.filter(scheduled__gte=datetime.date.today(),status='pending').last()
        if pending is None:
            # Check for a pending past date
            pending = self.visit_set.filter(status='pending').last()
            if pending is None:
                return None
        # Return the scheduled pending date
        return pending

    def tca_date(self):
        ''' Return To Come Again Date or None '''
        pending = self.next_visit()
        return pending.scheduled if pending is not None else None

    def tca_type(self):
        ''' Return next visit type '''
        pending = self.next_visit()
        return pending.visit_type.capitalize() if pending is not None else None

    def is_pregnant(self):
        return self.status == 'pregnant' or self.status == 'over'

    def was_pregnant(self,today=None):
        '''
        Returns true if the contact was pregnant at date today
        '''
        if self.delivery_date is not None:
            today = utils.today(today)
            return today <= self.delivery_date
        return True

    def delta_days(self,today=None):
        '''
        Return the number days until EDD or since delivery
        '''
        today = utils.today(today)
        if self.was_pregnant(today):
            if self.delivery_date is None:
                return (self.due_date - today).days
            else:
                return (self.delivery_date - today).days
        else: #post-partum
            # Return days since due date
            return (today-self.delivery_date).days

    def days_str(self,today=None):
        return utils.days_as_str(self.delta_days(today) )

    def description(self, **kwargs):
        """
        Description is a special formatted string that represents the state of a contact.
        It contains a series of dot-separated fields that map to the relevant attributes of the
        contact in determining an SMS message to send.

        Order of description: send_base.study_group.condition.hiv.second.offset

        See the equivalent section in the `AutomatedMessageQuerySet` class.
        """
        today = kwargs.get("today")

        condition = kwargs.get("condition",self.condition)
        group = kwargs.get("group",self.study_group)

        send_base = kwargs.get("send_base",'edd' if self.was_pregnant(today=today) else 'dd')
        send_offset = kwargs.get("send_offset",self.delta_days(today=today)/7)

        hiv_messaging = kwargs.get("hiv_messaging", self.hiv_messaging == "system")
        hiv = "Y" if hiv_messaging else "N"
        second_preg = kwargs.get('second_preg',self.second_preg)
        second = 'Y' if second_preg is True else 'N'

        # Special Case: Visit Messages
        if send_base == 'visit':
            hiv = "N"
            send_offset = 0
            second = 'N'

        # Special Case: SAE opt in messaging
        elif self.status == 'loss':
            today = utils.today(today)
            loss_offset = ((today - self.loss_date).days - 1)/7  + 1
            condition = 'nbaby'
            if loss_offset <= 4:
                send_base = 'loss'
                send_offset = loss_offset

        return "{send_base}.{group}.{condition}.{hiv}.{second}.{send_offset}".format(
            group=group, condition=condition, hiv=hiv, second=second,
            send_base=send_base , send_offset=send_offset,
        )

    def get_validation_key(self):
        # todo: what is this used by/for?
        sha = sha256('%s%s%s%s'%(self.study_id,self.nickname,self.anc_num,self.birthdate)).hexdigest()[:5]
        key = ''.join([str(int(i,16)) for i in sha])
        return key[:5]

    def choice_label(self):
        return '{} {}'.format(self.study_id,self.nickname)

    def add_call(self,outcome='answered',comment=None,length=None,is_outgoing=True,
                 created=None,admin_user=None,scheduled=None):
        if created is None:
            created = utils.today()
        else:
            created = utils.angular_datepicker(created)

        new_call = PhoneCall.objects.create(outcome=outcome,contact=self,is_outgoing=is_outgoing,
                        comment=comment,created=created,connection=self.connection(),length=length,
                        scheduled=scheduled)
        return new_call

    def delivery(self, delivery_date, comment='', user=None, source=None):
        self.delivery_date = delivery_date
        self.delivery_source = source

        # set_status calls self.save()
        self.set_status('post',comment='Post-partum set by {0}'.format(user))
        self.note_set.create(comment=comment,admin=user)

        # schedual 6w and 1yr call as needed
        self.schedule_month_call()
        self.schedule_year_call()

        # mark any delivery visits as attended
        self.visit_set.filter(visit_type='delivery').update(status='attended',arrived=delivery_date)

        # Add 6wk visits
        six_wk_date = delivery_date + datetime.timedelta(days=42)
        self.visit_set.create(scheduled=six_wk_date,visit_type='study')

    def set_status(self, new_status, comment='',note=False,user=None):
        old_status = self.status
        self.status = new_status
        self._old_status = new_status # Disable auto status change message
        self.save()

        self.statuschange_set.create(
            old = old_status, new = new_status, comment = comment
        )

        if note is True:
            self.note_set.create(comment=comment,admin=user)

    def schedule_month_call(self,created=False):
        ''' Schedule 1m call post delivery
                param: created(boolean): flag to return created,call tuple
            This function is idempotent
        '''

        if self.delivery_date is None:
            ''' No delivery date so call schedual post_edd call'''
            return self.schedule_edd_call(created)

        one_month_call = self.scheduledphonecall_set.filter(call_type='m').first()
        was_created = one_month_call is None

        if one_month_call is not None:
            # Already set a call 2w post edd
            if one_month_call.attended is not None:
                # Last schedualed call was made so do nothing
                # (assume it was the 14 day call were we learned about the delivery)
                pass
            else:
                # Delivery notification happes before posd-edd call
                # Change one month call to 30 days past delivery date
                one_month_call.scheduled = self.delilvery_date + datetime.timedelta(days=30)
        else:
            # Schedual call for one_month after delivery
            one_month_call = self.scheduledphonecall_set.create(
                scheduled=self.delivery_date+datetime.timedelta(days=30),
                call_type='m'
            )

        if created:
            return was_created , one_month_call
        return one_month_call

    def schedule_edd_call(self,created=False):
        ''' If no delivery date is set schedule a 14 day post edd call
                param: created(boolean): flag to return created,call tuple
            This function is idempotent
        '''
        if self.delivery_date is not None:
            # There is a delivery date so don't schedule an edd call
            if created:
                return False , None
            return None

        one_month_call = self.scheduledphonecall_set.filter(call_type='m').first()

        if one_month_call is not None:
            # Scheduled one month call has not been marked as attended
            if one_month_call.arrived is None:
                return False, one_month_call
            else:
                # Allready made a 14 day pre edd call so set for 14 days from now
                scheduled = datetime.date.today() + datetime.timedelta(days=14)
        else:
            # Set for 14 days from edd
            scheduled = self.due_date + datetime.timedelta(days=14)

        one_month_call = self.scheduledphonecall_set.create( scheduled=scheduled, call_type='m' )
        if created:
            return True , one_month_call
        return one_month_call

    def schedule_year_call(self,created=False):
        ''' Schedule 1yr calls as needed
                param: created(boolean): flag to return created,call tuple
            This function is idempotent
        '''
        one_year_call = self.scheduledphonecall_set.get_or_none(call_type='y')
        was_created = False

        if self.delivery_date is not None:
            if one_year_call is None:
                was_created = True
                one_year_call = self.scheduledphonecall_set.create(
                    scheduled=self.delivery_date+datetime.timedelta(days=365),
                    call_type='y'
                )
            else:
                one_year_call.scheduled = self.delivery_date+datetime.timedelta(days=365)

        if created:
            return was_created , one_year_call
        return one_year_call

    def message_kwargs(self):
        nurse_obj = Practitioner.objects.for_participant(self)
        return {
            'name':self.nickname.title(),
            'nurse':nurse_obj.user.first_name.title() if nurse_obj is not None else 'Nurse',
            'clinic':self.facility.title()
        }

    def send_message(self,text,control=False,**kwargs):

        # Control check - don't send messages to participants in the control
        if self.study_group == 'control' and control is False:
            text = 'CONTROL NOT SENT: ' + text
            msg_id = 'control'
            msg_success = False
            external_data = {}

        # Status check - don't send messages to participants with NO_SMS_STATUS
        elif self.status in Contact.NO_SMS_STATUS and control is False:
            text = 'STATUS {} NOT SENT: '.format(self.status.upper()) + text
            msg_id = self.status
            msg_success = False
            external_data = {}

        else:
            # Send message over system transport
            try:
                msg_id, msg_success, external_data = transports.send(self.phone_number(),text)
            except transports.TransportError as e:
                msg_id = ""
                msg_success = False
                external_data = {"error":str(e)}

        # Create new message
        new_message = self.message_set.create(
            text=text,
            connection=self.connection(),
            external_id=msg_id,
            external_success=msg_success,
            external_status="Sent" if msg_success else external_data.get("status","Failed"),
            external_data=external_data,
            **kwargs)

        return new_message

    def send_automated_message(self,control=False,send=True,exact=False,extra_kwargs=None,**kwargs):
        ''' kwargs get passed into self.description
            :param control bool - if True allow sending to control
            :param exact bool - if True only send exact match
            :param send bool - if True send message
            :kwargs
                - hiv_messaging bool - hiv_messaging or not
                - group - string for study group
                - today - date for sending to (default today)
                - send_base - string send_base
                - send_offset - int send_offset (or calculated from today)
                - condition - defaults to self.condition
        '''
        description = self.description(**kwargs)
        message = back.AutomatedMessage.objects.from_description(description,exact=exact)
        if message is None:
            return None #TODO: logging on this

        text = message.text_for(self,extra_kwargs)
        if text is None:
            return None #TODO: logging on this

        # Set last_msg_system
        self.last_msg_system = utils.today()
        self.save()

        if send:
            translated_text = message.english if self.language != 'english' else ''
            return self.send_message(
                text=text,
                translation_status='auto',
                auto=message.description(),
                control=control,
                translated_text=translated_text
            )
        else:
            return message

    ########################################
    # Reporting Functions
    ########################################

    def validation_delta(self):
        ''' Return the number of seconds between welcome message and validation '''
        if self.is_validated:
            welcome_msg = self.message_set.filter(auto__startswith='signup',auto__endswith='0').first()
            validation_msg = self.message_set.filter(topic='validation').last()
            if welcome_msg and validation_msg:
                delta = validation_msg.created - welcome_msg.created
                return delta.total_seconds()

    def delta_art(self):
        # return number of weeks between signup and art initiation
        if self.art_initiation is not None:
            return (self.created.date() - self.art_initiation).days / 7
        return None

    @property
    def sae_opt_in_status(self):
        if self.loss_date is not None:
            if self.status == 'loss':
                return 'in'
            elif self.status == 'sae':
                return 'out'
            elif self.statuschange_set.filter(new='loss').first() is not None:
                return 'in'
            elif self.statuschange_set.filter(new='sae').first() is not None:
                return 'out'
        return None

    _delivery_notification_delta = None
    @property
    def delivery_notification_delta(self):
        ''' Return the number of days between the delivery and delivery notification '''
        if self.delivery_date is None:
            return 0
        elif self._delivery_notification_delta is not None:
            return self._delivery_notification_delta
        else:
            status_change = self.statuschange_set.filter(type='status',new='post').last()
            if status_change is not None:
                self._delivery_notification_delta = (status_change.created.date() - self.delivery_date).days
            else:
                self._delivery_notification_delta = 0
            return self._delivery_notification_delta

    _loss_notification_delta = None
    @property
    def loss_notification_delta(self):
        ''' Return the number of days between a loss and when the study was notified '''
        if self.loss_date is None:
            return 0
        elif self._loss_notification_delta is not None:
            return self._loss_notification_delta
        else:
            status_change = self.statuschange_set.filter(type='status',new__in=['loss','sae']).last()
            if status_change is not None:
                self._loss_notification_delta =  (status_change.created.date() - self.loss_date).days
            else:
                self._loss_notification_delta = 0
            return self._loss_notification_delta

    @property
    def sim_count(self):
        if not hasattr(self,'_sim_count'):
            self._sim_count =  self.connection_set.count()
        return self._sim_count

    @property
    def stopped_study_delta(self):
        ''' Return the number of days between start of study and when a participant left '''
        status_change = self.statuschange_set.filter(type='status',new__in=('stopped','quite','other')).last()
        if status_change is not None:
            return (status_change.created - self.created).days
        return None

class StatusChangeQuerySet(ForUserQuerySet):

    participant_field = 'contact'

    def get_hiv_changes(self,td_kwargs=None):

        if td_kwargs is None:
            td_kwargs = {'hours':1}
        elif isinstance(td_kwargs,numbers.Number):
            td_kwargs = {'hours':td_kwargs}

        td = datetime.timedelta(**td_kwargs)
        hiv_status = self.filter(type='hiv').prefetch_related('contact')

        return [ s for s in hiv_status if s.created - s.contact.created > td ]

class StatusChange(TimeStampedModel):

    objects = StatusChangeQuerySet.as_manager()

    class Meta:
        app_label = 'contacts'

    contact = models.ForeignKey(settings.MESSAGING_CONTACT)

    old = models.CharField(max_length=20)
    new = models.CharField(max_length=20)
    type = models.CharField(max_length=10,default='status')

    comment = models.TextField(blank=True)

    def __str__(self):
        return "[{0.created_date}] {0.old} -> {0.new} ({0.type})".format(self)
