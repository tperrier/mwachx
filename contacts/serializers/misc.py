# From Django
from django.core.urlresolvers import reverse

# Rest Framework Imports
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import detail_route, api_view, list_route
from rest_framework.response import Response

#Local Imports
import contacts.models as cont
from messages import MessageSerializer

##############################################
# Facility Serializer and Viewset
##############################################

class FacilitySerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()

    class Meta:
        model = cont.Facility

    def get_name(self,obj):
        return ''.join(word.capitalize() for word in obj.name.split())

class FacilityViewSet(viewsets.ModelViewSet):

    queryset = cont.Facility.objects.all()
    serializer_class = FacilitySerializer

########################################
# Pending View
########################################

class PendingViewSet(viewsets.ViewSet):

    def list(self,request,format=None):
        pending = {
          'message_url':request.build_absolute_uri(reverse('pending-messages')),
          'messages':cont.Message.objects.pending().count(),
          'visits':0,
          'calls':0,
          'translations':10,
        }
        return Response(pending)

    @list_route()
    def messages(self,request):
        messages = cont.Message.objects.pending()
    	messages_seri = MessageSerializer(messages,many=True,context={'request':request})
        return Response(messages_seri.data)
