# Rest Framework Imports
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from django.utils import timezone

#Local Imports
import contacts.models as cont

#############################################
#  Serializers Definitions
#############################################

class ParticipantSimpleSerializer(serializers.ModelSerializer):

	status = serializers.CharField(source='get_status_display')
	study_group = serializers.CharField(source='get_study_group_display')
	phone_number = serializers.CharField()
	study_base_date = serializers.SerializerMethodField()
	href = serializers.HyperlinkedIdentityField(view_name='participant-detail',lookup_field='study_id')

	class Meta:
		model = cont.Contact
		fields = ('nickname','study_id','study_group','anc_num','phone_number', 'status','study_base_date','href')

	def get_study_base_date(self,obj):
		return obj.delivery_date or obj.due_date

class MessageSerializer(serializers.HyperlinkedModelSerializer):

	href = serializers.HyperlinkedIdentityField(view_name='message-detail')
	contact = ParticipantSimpleSerializer()

	class Meta:
		model = cont.Message
		fields = ('id','href','text','contact','translated_text','translation_status','is_outgoing','is_pending',
					'sent_by','is_related','topic','created')

#############################################
#  ViewSet Definitions
#############################################

class MessageViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	serializer_class = MessageSerializer
	queryset = cont.Message.objects.all().select_related('connection','contact').prefetch_related('contact__connection_set')

	@detail_route(methods=['put'])
	def dismiss(self, request, pk, *args, **kwargs):

		instance = self.get_object()
		instance.dismiss(**request.data)

		msg = MessageSerializer(instance,context={'request':request})
		return Response(msg.data)

	@detail_route(methods=['put'])
	def retranslate(self, request, pk, *args, **kwargs):

		instance = self.get_object()
		instance.translation_status = 'todo'
		instance.save()

		msg = MessageSerializer(instance,context={'request':request})
		return Response(msg.data)

	@detail_route(methods=['put'])
	def translate(self, request, pk, *args, **kwargs):

		instance = self.get_object()
		instance.translation_status = request.data['status']
		instance.languages = request.data['languages']

		if instance.translation_status == 'done':
			instance.translated_text = request.data['text']

		# Set translation time to now if it is currently none
		if instance.translation_time is None:
			instance.translation_time = timezone.now()

		instance.save()
		msg = MessageSerializer(instance,context={'request':request})
		return Response(msg.data)
