# Python Imports
import sys

# Rest Framework Imports
from rest_framework import viewsets
from rest_framework.response import Response

# Django Imports
from django.shortcuts import get_object_or_404

#Local Imports
import contacts.models as cont
from contacts.serializers.participants import ParticipantSerializer, ParticipantListSerializer
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

    def get_serializer_class(self):
        # Return the correct serializer based on current action
        if self.action == 'list':
            return ParticipantListSerializer
        else:
            return ParticipantSerializer


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
