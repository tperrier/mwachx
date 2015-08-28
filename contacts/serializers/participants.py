# Rest Framework Imports
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

#Local Imports
import contacts.models as cont
from messages import MessageSerializer
from visits import VisitSerializer

#############################################
#  Serializer Definitions
#############################################

class ParticipantListSerializer(serializers.ModelSerializer):
	# Foreign key example.
	# user = serializers.Field(source='user')
	status = serializers.SerializerMethodField()
	study_group = serializers.SerializerMethodField()
	phone_number = serializers.SerializerMethodField()
	url = serializers.HyperlinkedIdentityField(view_name='participant-detail',lookup_field='study_id')

	class Meta:
		model = cont.Contact
		fields = ('nickname','study_id','study_group', 'anc_num', 'status','phone_number','url')

	def get_status(self, obj):
		return obj.get_status_display()

	def get_study_group(self, obj):
		return obj.get_study_group_display()

	def get_phone_number(self, obj):
		return obj.phone_number

class ParticipantSerializer(serializers.ModelSerializer):
	status = serializers.SerializerMethodField()
	send_time = serializers.SerializerMethodField()
	send_day = serializers.SerializerMethodField()
	condition = serializers.SerializerMethodField()
	validation_key = serializers.SerializerMethodField()
	phone_number = serializers.SerializerMethodField()

	messages_url = serializers.HyperlinkedIdentityField(view_name='participant-messages',lookup_field='study_id')
	visits_url = serializers.HyperlinkedIdentityField(view_name='participant-visits',lookup_field='study_id')
	messages = MessageSerializer(source='message_set.top',many=True)
	visits = VisitSerializer(source='visit_set.top',many=True)

	class Meta:
		model = cont.Contact

	def get_phone_number(self, obj):
		return obj.phone_number

	def get_validation_key(self, obj):
		return obj.validation_key()

	def get_condition(self, obj):
		return obj.get_condition_display()

	def get_send_day(self, obj):
		return obj.get_send_day_display()

	def get_send_time(self, obj):
		return obj.get_send_time_display()

	def get_status(self, obj):
		return obj.get_status_display()

	def get_status(self, obj):
		return obj.get_status_display()

#############################################
#  ViewSet Definitions
#############################################

class ParticipantViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""

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

	@detail_route()
	def messages(self, request, study_id=None, *args, **kwargs):
		# Get Query Parameters
		limit = request.query_params.get('limit',None)
		max_id = request.query_params.get('max_id',None)
		min_id = request.query_params.get('min_id',None)

		# Create Message List and Serializer
		contact_messages = cont.Message.objects.filter(contact__study_id=study_id)
		if max_id:
		    contact_messages = contact_messages.filter(pk__lt=max_id)
		if min_id:
			contact_messages.filter(pk_gt=min_id)
		if limit:
		    contact_messages = contact_messages[:limit]
		contact_messages = MessageSerializer(contact_messages,many=True,context={'request':request})
		return Response(contact_messages.data)

	@detail_route()
	def visits(self, request, study_id=None, *args, **kwargs):
		contact_visits = cont.Visit.objects.filter(contact__study_id=study_id)
		contact_visits = VisitSerializer(contact_visits,many=True,context={'request':request})
		return Response(contact_visits.data)
