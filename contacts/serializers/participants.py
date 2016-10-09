# Python Imports
import json, datetime

# Django imports
from django.utils import timezone
from django.db import transaction, models

# Rest Framework Imports
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework import status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

#Local Imports
import contacts.models as cont
import backend.models as back
import contacts.forms as forms
import utils

from messages import MessageSerializer, ParticipantSimpleSerializer, MessageSimpleSerializer
from visits import VisitSimpleSerializer , VisitSerializer
from misc import PhoneCallSerializer, NoteSerializer

#############################################
#  Serializer Definitions
#############################################

class ParticipantSerializer(serializers.ModelSerializer):
	status_display = serializers.CharField(source='get_status_display')

	send_time_display = serializers.CharField(source='get_send_time_display')
	send_time = serializers.CharField()
	send_day_display = serializers.CharField(source='get_send_day_display')
	send_day = serializers.CharField()

	condition = serializers.CharField(source='get_condition_display')
	validation_key = serializers.CharField()
	phone_number = serializers.CharField()
	facility = serializers.CharField(source='get_facility_display')
	age = serializers.CharField(read_only=True)
	is_pregnant = serializers.BooleanField(read_only=True)
	active = serializers.BooleanField(read_only=True,source='is_active')

	hiv_disclosed_display = serializers.SerializerMethodField()
	hiv_disclosed = serializers.SerializerMethodField()
	hiv_messaging_display = serializers.CharField(source='get_hiv_messaging_display')
	hiv_messaging = serializers.CharField()

	href = serializers.HyperlinkedIdentityField(view_name='participant-detail',lookup_field='study_id')
	messages_url = serializers.HyperlinkedIdentityField(view_name='participant-messages',lookup_field='study_id')
	visits_url = serializers.HyperlinkedIdentityField(view_name='participant-visits',lookup_field='study_id')
	calls_url = serializers.HyperlinkedIdentityField(view_name='participant-calls',lookup_field='study_id')
	notes_url = serializers.HyperlinkedIdentityField(view_name='participant-notes',lookup_field='study_id')

	# TODO: Change calls to call count and remove messages and visits
	# calls = PhoneCallSerializer(source='phonecall_set',many=True)
	# messages = MessageSerializer(source='get_pending_messages',many=True)
	visits = VisitSimpleSerializer(source='pending_visits',many=True)

	phonecall_count = serializers.SerializerMethodField()
	note_count = serializers.SerializerMethodField()

	class Meta:
		model = cont.Contact

	def get_hiv_disclosed_display(self,obj):
		return utils.null_boolean_display(obj.hiv_disclosed)

	def get_hiv_disclosed(self,obj):
		return utils.null_boolean_form_value(obj.hiv_disclosed)

	def get_note_count(self,obj):
		try:
			return getattr(obj,'note_count')
		except AttributeError as e:
			return obj.note_set.count()

	def get_phonecall_count(self,obj):
		try:
			return getattr(obj,'phonecall_count')
		except AttributeError as e:
			return obj.phonecall_set.count()


#############################################
#  ViewSet Definitions
#############################################

class ParticipantViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""

	lookup_field = 'study_id'

	def get_queryset(self):
		qs = cont.Contact.objects.all().order_by('study_id')
		# Only return the participants for this user's facility
		if self.action == 'list':
			return qs.for_user(self.request.user,superuser=True)
		else:
			# return qs
			return qs.prefetch_related('phonecall_set')

	def get_serializer_class(self):
	    # Return the correct serializer based on current action
	    if self.action == 'list':
	        return ParticipantSimpleSerializer
	    else:
	        return ParticipantSerializer

	########################################
	# Overide Router POST, PUT, PATCH
	########################################

	def create(self, request, *args, **kwargs):
		''' POST - create a new participant '''
		cf = forms.ContactAdd(request.data)

		if cf.is_valid():
			with transaction.atomic():
				#Create new contact but do not save in DB
				contact = cf.save(commit=False)

				#Set contacts facility to facility of current user
				facility = '' # Default to blank facility if none found
				try:
					facility = request.user.practitioner.facility
				except cont.Practitioner.DoesNotExist:
					pass

				contact.facility = facility
				contact.validation_key = contact.get_validation_key()
				#Important: save before making foreign keys
				contact.save()

				phone_number = '+254%s'%cf.cleaned_data['phone_number'][1:]
				cont.Connection.objects.create(identity=phone_number,contact=contact,is_primary=True)

				# Set the next visits
				if cf.cleaned_data['clinic_visit']:
					cont.Visit.objects.create(scheduled=cf.cleaned_data['clinic_visit'],
						participant=contact,visit_type='clinic')
				if cf.cleaned_data['due_date']:
					# Set first study visit to 6 weeks (42 days) after EDD
					cont.Visit.objects.create(scheduled=cf.cleaned_data['due_date']+datetime.timedelta(days=42),
						participant=contact,visit_type='study')

				#Send Welcome Message
				contact.send_automated_message(send_base='signup',send_offset=0,
					control=True,hiv_messaging=False)

			serialized_contact = ParticipantSerializer(contact,context={'request':request})
			return Response(serialized_contact.data)

		else:
			return Response({ 'errors': json.loads(cf.errors.as_json()) })

	# TODO: Edit this to watch for status changes
	def partial_update(self, request, study_id=None, *args, **kwargs):
		''' PATCH - partial update a participant '''

		instance = self.get_object()

		instance.status = request.data['status']
		instance.send_time = request.data['send_time']
		instance.send_day = request.data['send_day']
		instance.art_initiation = utils.angular_datepicker(request.data['art_initiation'])
		instance.due_date = utils.angular_datepicker(request.data['due_date'])
		instance.hiv_disclosed = request.data['hiv_disclosed']
		instance.hiv_messaging = request.data['hiv_messaging']

		instance.save()
		instance_serialized = ParticipantSerializer(cont.Contact.objects.get(pk=instance.pk),context={'request':request}).data
		return Response(instance_serialized)

	@detail_route(methods=['post','get'])
	def messages(self, request, study_id=None, *args, **kwargs):
		if request.method == 'GET':
			# Get Query Parameters
			limit = request.query_params.get('limit',None)
			max_id = request.query_params.get('max_id',None)
			min_id = request.query_params.get('min_id',None)

			# Create Message List and Serializer
			contact_messages = cont.Message.objects.filter(contact__study_id=study_id).select_related('connection__contact','contact').prefetch_related('contact__connection_set')
			if max_id:
			    contact_messages = contact_messages.filter(pk__lt=max_id)
			if min_id:
				contact_messages.filter(pk_gt=min_id)
			if limit:
			    contact_messages = contact_messages[:limit]
			contact_messages = MessageSimpleSerializer(contact_messages,many=True,context={'request':request})
			return Response(contact_messages.data)

		elif request.method == 'POST':
			'''A POST to participant/:study_id:/messages sends a new message to that participant'''
			# print 'Participant Message Post: ',request.data
			participant = self.get_object()
			message = {
				'text':request.data['message'],
				'languages':request.data['languages'],
				'translation_status':request.data['translation_status'],
				'is_system':False,
				'is_viewed':False,
				'admin_user':request.user,
				'control':True,
			}

			if message['translation_status'] == 'done':
				message['translated_text'] = request.data['translated_text']

			if request.data.has_key('reply'):
				message['parent'] = cont.Message.objects.get(pk=request.data['reply']['id'])
				message['parent'].action_time = timezone.now()

				if message['parent'].is_pending:
					message['parent'].dismiss(**request.data['reply'])
				message['parent'].save()

			new_message = participant.send_message(**message)


			return Response(MessageSerializer(new_message,context={'request': request}).data)

	@detail_route(methods=['get','post'])
	def calls(self, request, study_id=None):
		if request.method == 'GET': # Return serialized call history
			call_history = cont.PhoneCall.objects.filter(contact__study_id=study_id)
			call_serialized = PhoneCallSerializer(call_history,many=True,context={'request':request})
			return Response(call_serialized.data)
		elif request.method == 'POST': # Save a new call
			participant = self.get_object()
			new_call = participant.add_call(**request.data)
			new_call_serialized = PhoneCallSerializer(new_call,context={'request':request})
			return Response(new_call_serialized.data)

	@detail_route(methods=['get','post'])
	def visits(self, request, study_id=None, *args, **kwargs):
		if request.method == 'GET': # Return a serialized list of all visits

			instance = self.get_object()
			visits = instance.visit_set.exclude(status='deleted')
			visits_serialized = VisitSerializer(visits,many=True,context={'request':request})
			return Response(visits_serialized.data)

		elif request.method == 'POST': # Schedual a new visit

			instance = self.get_object()
			next_visit = instance.visit_set.create(
				scheduled=utils.angular_datepicker(request.data['next']),
				visit_type=request.data['type']
			)
			return Response(VisitSerializer(next_visit,context={'request':request}).data)

	@detail_route(methods=['get','post'])
	def notes(self, request, study_id=None):
		if request.method == 'GET': # Return a serialized list of all notes

			notes = cont.Note.objects.filter(participant__study_id=study_id)
			notes_serialized = NoteSerializer(notes,many=True,context={'request',request})
			return Response(notes_serialized.data)

		elif request.method == 'POST': # Add a new note

			note = cont.Note.objects.create(participant=self.get_object(),admin=request.user,comment=request.data['comment'])
			note_serialized	= NoteSerializer(note,context={'request',request})
			return Response(note_serialized.data)


	@detail_route(methods=['put'])
	def delivery(self, request, study_id=None):

		instance = self.get_object()
		if not instance.is_pregnant():
			return Response({'error':{'message':'Participant already post-partum'}})

		comment = "Delivery notified via {0}. \n{1}".format(request.data.get('source'),request.data.get('comment',''))
		delivery_date = utils.angular_datepicker(request.data.get('delivery_date'))
		instance.delivery(delivery_date, comment=comment, user=request.user, source=request.data['source'])

		serializer = self.get_serializer(instance)
		return Response(serializer.data)

	@detail_route(methods=['put'])
	def stop_messaging(self, request, study_id=None):
		reason = request.data.get('reason','')
		sae = request.data.get('sae',False)

		instance = self.get_object()

		if sae is True:
			receive_sms = request.data.get('receive_sms',False)
			loss_date = utils.angular_datepicker(request.data.get('loss_date'))
			note=False

			status = 'loss' if receive_sms else 'sae'
			comment = "Changed loss opt-in status: {}".format(receive_sms)
			if instance.loss_date is None:
				# Set loss date if not set
				instance.loss_date = loss_date
				if instance.delivery_date is None:
					# Set delivery date to loss date if not already set
					instance.delivery_date = loss_date
				comment = "{}\nSAE event recorded by {}. Opt-In: {}".format(reason,request.user.practitioner,receive_sms)
				note=True

			print "SAE {} continue {}".format(loss_date,receive_sms)
			instance.set_status(status,comment=comment,note=note,user=request.user)

		elif instance.status == 'other':
			comment = "{}\nMessaging changed in web interface by {}".format(reason,request.user.practitioner)
			status = 'pregnant' if instance.delivery_date is None else 'post'
			instance.set_status(status, comment=comment)
		else:
			comment = "{}\nStopped in web interface by {}".format(reason,request.user.practitioner)
			instance.set_status('other', comment=comment)

		serializer = self.get_serializer(instance)
		return Response(serializer.data)
