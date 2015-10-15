# Python Imports
import datetime

# Rest Framework Imports
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

#Local Imports
import contacts.models as cont
from messages import ParticipantSimpleSerialier

class VisitSerializer(serializers.ModelSerializer):

    href = serializers.HyperlinkedIdentityField(view_name='visit-detail')
    participant = ParticipantSimpleSerialier()

    class Meta:
        model = cont.Visit
        fields = ('id','href','participant','scheduled','arrived','notification_last_seen','skipped',
                  'comment','visit_type','days_overdue')

class VisitViewSet(viewsets.ModelViewSet):

    queryset =  cont.Visit.objects.all()
    serializer_class = VisitSerializer

    @detail_route(methods=['put'])
    def seen(self, request, pk):

        instance = self.get_object()
        instance.seen()

        visit = VisitSerializer(instance,context={'request':request})
        return Response(visit.data)

    @detail_route(methods=['put'])
    def attended(self, request, pk):

        instance = self.get_object()
        instance.attended(datetime.datetime.strptime(request.data.get('arrived',None),'%Y-%m-%d').date())
        instance_serialized = VisitSerializer(instance,context={'request':request}).data

        # Make next visit if needed
        next_visit_serialized = {}
        if request.data.has_key('next'):
            next_visit = cont.Visit.objects.create(
                participant=instance.participant,
                scheduled=datetime.datetime.strptime(request.data['next'],'%Y-%m-%d').date(),
                visit_type=request.data['type']
            )
            next_visit_serialized = VisitSerializer(next_visit,context={'request':request}).data

        return Response({'visit':instance_serialized,'next':next_visit_serialized})
