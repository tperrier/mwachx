# Rest Framework Imports
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

#Local Imports
import contacts.models as cont
from messages import ParticipantSimpleSerialier

class VisitSerializer(serializers.ModelSerializer):

    participant = ParticipantSimpleSerialier()

    class Meta:
        model = cont.Visit
        exclude = ('created','modified')

class VisitViewSet(viewsets.ModelViewSet):

    queryset =  cont.Visit.objects.all()
    serializer_class = VisitSerializer
