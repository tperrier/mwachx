from rest_framework import viewsets

#Local Imports
import contacts.models as cont
from contacts.serializers.participants import ParticipantSerializer

class ParticipantViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = cont.Contact.objects.all()
    serializer_class = ParticipantSerializer
