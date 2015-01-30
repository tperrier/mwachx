import models as cont

def receive(number,message):
    '''
    Main hook for receiving messages
        * number: the phone number of the incoming message
        * message: the text of the incoming message
    '''
    
    connection,created = cont.Connection.get_or_create(identity=number)
    cont.Message.create(
        is_system=False,
        is_outgoing=False,
        text=message,
        connection=connection,
        contact=connection.contact
    )
    
