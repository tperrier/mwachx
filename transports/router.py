# Django imports
from django.conf import settings

# Local imports
import contacts.models as cont
import validation

def send(identity, message, transport_name=None):
    ''' Main hook for sending message to identity.
        If transport_name is None will use settings.SMS_TRANSPORT or default
    '''
    # Find name of transport module
    if transport_name is None:
        transport_name = getattr(settings,'transport',None)
    if transport_name is None:
        transport_name = 'default'

    # Get transport send Function
    transport = __import__(transport_name,globals(),locals())
    transport.send(identity,message)

def receive(identity,message,external_id=None,**kwargs):
    '''
    Main hook for receiving messages
        * identity: the phone number of the incoming message
        * message: the text of the incoming message
        * external_id: id associated with external transport
        * kwargs: dict of extra data associated with transport
    '''
    #Get incoming connection or create if not found
    connection,created = cont.Connection.objects.get_or_create(identity=identity)
    contact = None if created else connection.contact

    for validator in validation.validators:
        if validator(contact,message):
            validator.action(contact)
            break

    return cont.Message.objects.create(
        is_system=False,
        is_outgoing=False,
        text=message,
        connection=connection,
        contact=contact,
        external_id=external_id,
        external_data=kwargs
    )

class TransportError(Exception):
    pass
