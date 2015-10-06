# Rest Framework Imports
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.response import Response

#Local Imports
import contacts.models as cont

#############################################
#  Serializers Definitions
#############################################

class ParticipantSimpleSerialier(serializers.ModelSerializer):

	status = serializers.SerializerMethodField()
	study_group = serializers.SerializerMethodField()
	phone_number = serializers.SerializerMethodField()
	href = serializers.HyperlinkedIdentityField(view_name='participant-detail',lookup_field='study_id')

	class Meta:
		model = cont.Contact
		fields = ('nickname','study_id','study_group', 'status','phone_number','href')

	def get_status(self, obj):
		return obj.get_status_display()

	def get_study_group(self, obj):
		return obj.get_study_group_display()

	def get_phone_number(self, obj):
		return obj.phone_number

class MessageSerializer(serializers.HyperlinkedModelSerializer):

	href = serializers.HyperlinkedIdentityField(view_name='message-detail')
	contact = ParticipantSimpleSerialier()

	class Meta:
		model = cont.Message
		fields = ('id','href','text','contact','translated_text','is_translated','is_pending',
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
