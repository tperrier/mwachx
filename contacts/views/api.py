from rest_framework import viewsets

#Local Imports
import contacts.models as cont
from contacts.serializers.participants import ParticipantSerializer
from contacts.serializers.messages import MessageSerializer

class ParticipantViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    serializer_class = ParticipantSerializer
    lookup_field = 'study_id'

    def get_queryset(self):
    	# Only return the participants for this user's facility
    	return cont.Contact.objects.for_user(self.request.user).all()


class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    serializer_class = MessageSerializer

    def get_queryset(self):
    	# Only return the participants for this user's facility
    	return cont.Message.objects.for_user(self.request.user).all()
