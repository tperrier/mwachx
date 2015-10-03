# Python Imports
import json

# Rest Framework Imports
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

#Local Imports
import contacts.models as cont
import contacts.forms as forms
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
	href = serializers.HyperlinkedIdentityField(view_name='participant-detail',lookup_field='study_id')

	class Meta:
		model = cont.Contact
		fields = ('nickname','study_id','study_group', 'anc_num', 'status','phone_number','href')

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

	href = serializers.HyperlinkedIdentityField(view_name='participant-detail',lookup_field='study_id')
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

	########################################
	# Overide Router POST, PUT, PATCH
	########################################

	def create(self, request, *args, **kwargs):
		''' POST - create a new participant '''
		cf = forms.ContactAdd(request.data)
		if cf.is_valid():
			#Create new contact but do not save in DB
			contact = cf.save(commit=False)

			#Set contacts facility to facility of current user
			facility = cont.Facility.objects.get(pk=1) #default to first facility if none found
			try:
				facility = request.user.practitioner.facility
			except cont.Practitioner.DoesNotExist:
				pass

			contact.facility = facility
			#Important: save before making foreign keys
			contact.save()

			phone_number = '+254%s'%cf.cleaned_data['phone_number'][1:]
			cont.Connection.objects.create(identity=phone_number,contact=contact,is_primary=True)

			'''
			#Send Welcome Message
			message = 'Welcome to the mWaCh X Study. Please send your five letter confirmation code'
			cont.Message.send(contact,message,'',translate_skipped=True)
			'''

			serialized_contact = ParticipantSerializer(contact,context={'request':request})
			return Response(serialized_contact.data)

		else:
			return Response({'message':'post - create',
					'errors':json.loads(cf.errors.as_json()),
					'data':request.data,
					'valid':cf.is_valid()})

	def update(self, request, study_id=None, *args, **kwargs):
		''' PUT - full update a new participant '''
		return Response({'message':'put - update','data':request.data})

	def partial_update(self, request, study_id=None, *args, **kwargs):
		''' PATCH - partial update a participant '''
		return Response({'message':'patch - partial update','data':request.data})

	@detail_route(methods=['post','get'])
	def messages(self, request, study_id=None, *args, **kwargs):
		if request.method == 'GET':
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
		elif request.method == 'POST':
			print request.data
			participant = self.get_object()
			new_message = participant.send_message(request.data['text'])
			return Response(MessageSerializer(new_message,context={'request': request}).data)


	@detail_route()
	def visits(self, request, study_id=None, *args, **kwargs):
		contact_visits = cont.Visit.objects.filter(contact__study_id=study_id)
		contact_visits = VisitSerializer(contact_visits,many=True,context={'request':request})
		return Response(contact_visits.data)
