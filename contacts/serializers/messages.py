# Rest Framework Imports
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.response import Response

#Local Imports
import contacts.models as cont

#############################################
#  Serializers Definitions
#############################################

class MessageSerializer(serializers.HyperlinkedModelSerializer):

	href = serializers.HyperlinkedIdentityField(view_name='message-detail')

	class Meta:
		model = cont.Message
		fields = ('id','href','text','translated_text','is_translated','is_pending',
					'is_system','is_outgoing','created')

#############################################
#  ViewSet Definitions
#############################################

class MessageViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	serializer_class = MessageSerializer
	queryset = cont.Message.objects.all()
