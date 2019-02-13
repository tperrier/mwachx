import datetime
# Django imports
from django.conf import settings

# Local imports
import validation

def send(identity, message, transport_name=None):
    ''' Main hook for sending message to identity.
        If transport_name is None will use settings.SMS_TRANSPORT or default
    '''
    # Find name of transport module
    if transport_name is None:
        transport_name = getattr(settings,'SMS_TRANSPORT','default')

    # Get transport send Function
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
    '''
    #Get incoming connection or create if not found
    from contacts import models as cont
    connection,created = cont.Connection.objects.get_or_create(identity=identity)
    contact = None if created else connection.contact
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

class TransportError(Exception):
    pass
