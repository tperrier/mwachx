from django.conf import settings

def send(identity, message, transport_name=None):
    # Find name of transport module
    if transport_name is None:
        transport_name = getattr(settings,'transport',None)
    if transport_name is None:
        transport_name = 'default'

    # Get transport send Function
    transport = __import__(transport_name,globals(),locals())
    transport.send(identity,message)

class TransportError(Exception):
    pass
