import datetime
# Django imports
from django.conf import settings

# Local imports
import contacts.models as cont
import transports.models as trans
import validation

def send(identity, message, transport_name=None):
    ''' Main hook for sending message to identity.
        If transport_name is None will use settings.SMS_TRANSPORT or default
    '''
    # Import transport module
    if transport_name is None:
        # Find name of transport module
        transport_name = getattr(settings,'SMS_TRANSPORT','default')
    transport = __import__(transport_name,globals(),locals())

    id, success, data = transport.send(identity,message)
    return id, success, data

def receive(identity,message_text,external_id='',**kwargs):
    '''
    Main hook for receiving messages
        * identity: the phone number of the incoming message
        * message_text: the text of the incoming message
        * external_id: id associated with external transport
        * kwargs: dict of extra data associated with transport

    Returns: a Message or FowardMessage object
    '''
    sms_forward_url = getattr(settings,'SMS_FORWARD_URL',None)
    if sms_forward_url is not None:
        connection = cont.Connection.objects.get_or_none(identity=identity)
        if connection is None:
            return forward_message(identity,message_text,external_id,**kwargs)
        return receive_message(connection,message_text,external_id,**kwargs)
    else:
        #Get incoming connection or create if not found
        connection,created = cont.Connection.objects.get_or_create(identity=identity)
        return receive_message(connection,message_text,external_id,**kwargs)

def receive_message(connection,message_text,external_id,**kwargs):
    contact = getattr(connection,'contact',None)
    message = cont.Message(
        is_system=False,
        is_outgoing=False,
        text=message_text.strip(),
        connection=connection,
        contact=contact,
        external_id=external_id,
        external_data=kwargs,
    )

    if contact:
        for validator in validation.validators:
            valid = validator(message)
            if valid:
                if validator.action(message) is False:
                    break

        # Set last_msg_client
        contact.last_msg_client = datetime.date.today()
        contact.save()

    message.save()
    return message

def forward_message(identity,message_text,external_id,**kwargs):
    # Foward message using forward transport and log in transport message log

    # Import transport module
    transport_name = getattr(settings,'SMS_FORWARD_TRANSPORT','default')
    transport = __import__(transport_name,globals(),locals())


    try:
        fwrd_status = transport.forward(identity,message_text,external_id,**kwargs)
    except AttributeError as e:
        # forward function not found
        fwrd_status = 'none'

    # Save message in transport foward log
    sms_forward_url = getattr(settings,'SMS_FORWARD_URL',None)
    msg = trans.ForwardMessage.objects.create(
        identity=identity,
        text=message_text.strip(),
        transport=transport_name,
        url=sms_forward_url,
        fwrd_status=fwrd_status,
        external_id=external_id,
        external_data=kwargs
    )

    return msg

class TransportError(Exception):
    pass
