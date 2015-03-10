from rest_framework import viewsets
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

#Local Imports
import contacts.models as cont
from contacts.serializers.participants import ParticipantSerializer, ParticipantDetailSerializer
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

    def retrieve(self, request, study_id=None):
        # Use the detailed serializer for individual GETs
        queryset = self.get_queryset()
        user = get_object_or_404(queryset, study_id=study_id)
        serializer = ParticipantDetailSerializer(user)
        return Response(serializer.data)


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
        # Only return the messages for this user's facility
        return cont.Contact.objects.for_user(self.request.user).all()