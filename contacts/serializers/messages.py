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
    href = serializers.HyperlinkedIdentityField(view_name='participant-detail', lookup_field='study_id')
    next_visit_date = serializers.SerializerMethodField()
    next_visit_type = serializers.SerializerMethodField()

    class Meta:
        # todo: can this be changed to a swappable version?
        model = cont.Contact
        fields = ('nickname', 'study_id', 'study_group', 'anc_num', 'phone_number', 'status',
                  'study_base_date', 'last_msg_client', 'href', 'next_visit_date', 'next_visit_type')

    def get_study_base_date(self, obj):
        return obj.delivery_date or obj.due_date

    def get_next_visit_date(self, obj):
        try:
            return obj.pending_visits[0].scheduled
        except IndexError as e:
            return None
        except AttributeError as e:
            return obj.tca_date()

    def get_next_visit_type(self, obj):
        try:
            return obj.pending_visits[0].visit_type
        except IndexError as e:
            return 'none'
        except AttributeError as e:
            return obj.tca_type()


class MessageSerializer(serializers.HyperlinkedModelSerializer):
    href = serializers.HyperlinkedIdentityField(view_name='message-detail')
    contact = ParticipantSimpleSerializer()

    class Meta:
        model = cont.Message
        fields = (
        'id', 'href', 'text', 'contact', 'translated_text', 'translation_status', 'is_outgoing', 'is_pending',
        'sent_by', 'is_related', 'topic', 'created')


class MessageSimpleSerializer(serializers.HyperlinkedModelSerializer):
    href = serializers.HyperlinkedIdentityField(view_name='message-detail')

    class Meta:
        model = cont.Message
        fields = ('id', 'href', 'text', 'translated_text', 'translation_status', 'is_outgoing', 'is_pending',
                  'sent_by', 'is_related', 'topic', 'created')


#############################################
#  ViewSet Definitions
#############################################

class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    serializer_class = MessageSerializer
    queryset = cont.Message.objects.all().select_related('connection', 'contact').prefetch_related(
        'contact__connection_set')

    @detail_route(methods=['put'])
    def dismiss(self, request, pk, *args, **kwargs):

        instance = self.get_object()
        instance.dismiss(**request.data)

        msg = MessageSerializer(instance, context={'request': request})
        return Response(msg.data)

    @detail_route(methods=['put'])
    def retranslate(self, request, pk, *args, **kwargs):

        instance = self.get_object()
        instance.translation_status = 'todo'
        instance.save()

        msg = MessageSerializer(instance, context={'request': request})
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
        msg = MessageSerializer(instance, context={'request': request})
        return Response(msg.data)
