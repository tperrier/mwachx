# Python Imports
import datetime

# Rest Framework Imports
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

#Local Imports
import contacts.models as cont
from messages import ParticipantSimpleSerializer
import utils

class VisitSerializer(serializers.ModelSerializer):

    href = serializers.HyperlinkedIdentityField(view_name='visit-detail')
    participant = ParticipantSimpleSerializer()

    status = serializers.SerializerMethodField()
    days_str = serializers.CharField()
    is_pregnant = serializers.BooleanField(read_only=True)

    visit_type = serializers.CharField(source='get_visit_type_display')


    class Meta:
        model = cont.Visit
        fields = ('id','href','participant','scheduled','arrived','notification_last_seen','status',
                  'comment','visit_type','days_overdue','days_str','is_pregnant')

    def get_status(self,obj):
        return obj.get_status_display()

class VisitViewSet(viewsets.ModelViewSet):

    queryset =  cont.Visit.objects.all()
    serializer_class = VisitSerializer

    @list_route()
    def upcoming(self, request):
        queryset = self.queryset.for_user(request.user).visit_range(start={'days':-14},end={'days':0}).order_by('scheduled')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @detail_route(methods=['put'])
    def seen(self, request, pk):

        instance = self.get_object()
        instance.seen()

        cont.EventLog.objects.create(user=request.user,event='visit.seen',data={'visit_id':instance.id})

        visit = VisitSerializer(instance,context={'request':request})
        return Response(visit.data)

    @detail_route(methods=['put'])
    def attended(self, request, pk):

        instance = self.get_object()
        instance.attended(request.data.get('arrived',None))
        instance_serialized = VisitSerializer(instance,context={'request':request}).data

        cont.EventLog.objects.create(user=request.user,event='visit.attended',data={'visit_id':instance.id})

        # Make next visit if needed
        next_visit_serialized = None
        if request.data.has_key('next'):
            print 'Next Visit',request.data['next']
            next_visit = instance.participant.visit_set.create(
                scheduled=utils.angular_datepicker(request.data['next']),
                visit_type=request.data['type']
            )
            next_visit_serialized = VisitSerializer(next_visit,context={'request':request}).data

        return Response({'visit':instance_serialized,'next':next_visit_serialized})

    @detail_route(methods=['put'])
    def missed(self, request, pk):

        instance = self.get_object()
        instance.set_status('missed')
        instance_serialized = VisitSerializer(instance,context={'request':request}).data

        return Response(instance_serialized)

    @detail_route(methods=['put'])
    def edit(self, request, pk):

        instance = self.get_object()
        instance.scheduled = utils.angular_datepicker(request.data['scheduled'])
        instance.save()

        instance_serialized = self.get_serializer(instance)
        return Response(instance_serialized.data)

    def destroy(self, request, pk):

        instance = self.get_object()
        instance.set_status('deleted')

        instance_serialized = self.get_serializer(instance)
        return Response(instance_serialized.data)
