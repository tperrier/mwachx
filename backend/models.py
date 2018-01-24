from django.db import models
from utils import enums

import utils.models as utils


class AutomatedMessageQuerySet(utils.BaseQuerySet):
    """
    Used to map a single description to an AutomatedMessage.
    """

    def from_description(self, description, exact=False):
        """
        Return AutomatedMessage for description

        :param description (str): base.condition.offset string to look for
        :returns: AutomatedMessage matching description or closes match if not found
        """
        send_base, condition, send_offset = description.split('.')
        send_offset = int(send_offset)

        # # Special case for post date messages go back and forth between week 41 and 42 messages
        # if send_base == 'edd' and send_offset > 2:
        #     send_offset = (send_offset+1)%-2 - 1

        return self.from_parameters(send_base,condition,send_offset,exact=exact)

    def from_parameters(self,send_base,condition='normal',send_offset=0,exact=False):

        # Look for exact match of parameters
        try:
            return self.get(send_base=send_base, send_offset=send_offset, condition=condition)
        except AutomatedMessage.DoesNotExist as e:
            if exact == True:
                return None
            # No match for participant conditions continue to find best match
            pass

        # Create the base query set with send_base and offset
        message_offset = self.filter(send_base=send_base,send_offset=send_offset)

        if condition != "normal":
            # Force condition to normal and try again
            try:
                return message_offset.get(condition="normal")
            except AutomatedMessage.DoesNotExist as e:
                pass

        return message_offset.filter(condition='normal').first()

    def from_excel(self,msg):
        """
        Replace fields of message content with matching description
        """
        auto = self.from_description(msg.description(),exact=True)
        if auto is None:
            return self.create(**msg.kwargs()) , 'created'
        else:
            msg_english = msg.english if msg.english != '' else msg.new
            changed = msg_english != auto.english or msg.swahili != auto.swahili or msg.luo != auto.luo

            auto.english = msg_english
            auto.swahili = msg.swahili
            auto.luo = msg.luo
            auto.todo = msg.status == 'todo'
            auto.save()

            return auto, 'changed' if changed else 'same'


class AutomatedMessage(models.Model):
    """
    Automated Messages for sending to participants. These represent message _templates_
    not message _instances_.
    """

    SEND_BASES_CHOICES = (
        ('edd','Before EDD'),
        ('over','Post Dates'),
        ('dd','Postpartum'),
        ('visit','Visit'),
        ('signup','From Signup'),
        ('connect','Reconnect'),
        ('bounce','Bounce'),
        ('loss','Loss'),
        ('stop','Stop'),
    )

    CONDITION_CHOICES = (
        ('art','Starting ART'),
        ('adolescent','Adolescent'),
        ('first','First Time Mother'),
        ('normal','Normal'),
        ('nbaby','No Baby'),
    )

    class Meta:
        app_label = 'backend'

    objects = AutomatedMessageQuerySet.as_manager()

    priority = models.IntegerField(default=0)

    english = models.TextField(blank=True)
    swahili = models.TextField(blank=True)
    luo = models.TextField(blank=True)

    comment = models.TextField(blank=True)

    # group = models.CharField(max_length=20,choices=enums.GROUP_CHOICES)  # 2 groups
    condition = models.CharField(max_length=20,choices=CONDITION_CHOICES)  # 4 conditions

    send_base = models.CharField(max_length=20,help_text='Base to send messages from',choices=SEND_BASES_CHOICES)
    send_offset = models.IntegerField(default=0,help_text='Offset from base in days')

    todo = models.BooleanField()

    def category(self):
        return "{0.send_base}.{0.condition}".format(self)

    def description(self):
        return "{0}.{1}".format(self.category(),self.send_offset)

    def text_for(self,participant,extra_kwargs=None):
        text = self.get_language(participant.language)

        message_kwargs = participant.message_kwargs()
        if extra_kwargs is not None:
            message_kwargs.update(extra_kwargs)
        return text.format(**message_kwargs)

    def get_language(self,language):
        # TODO: Error checking
        return getattr(self,language)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<AutomatedMessage: {}>".format(self.description())
