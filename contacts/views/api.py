from rest_framework import viewsets
from rest_framework.response import Response

#Local Imports
import contacts.models as cont
from contacts.serializers.participants import ParticipantSerializer
from contacts.serializers.messages import MessageSerializer

import logging, logging.config
import sys

LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO'
    }
}

logging.config.dictConfig(LOGGING)
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

    def list(self, request):
        # Only return the messages for this user's facility
        # if "study_id" in request
        if "study_id" in request.GET:
            queryset = cont.Message.objects.for_user(self.request.user).filter(contact__study_id=request.GET["study_id"])
        elif "study_id" in request.POST:
            queryset = cont.Message.objects.for_user(self.request.user).filter(contact__study_id=request.GET["study_id"])
        else:
            queryset = cont.Message.objects.for_user(self.request.user).all()
        serializer = MessageSerializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        # Only return the participants for this user's facility
        return cont.Contact.objects.for_user(self.request.user).all()