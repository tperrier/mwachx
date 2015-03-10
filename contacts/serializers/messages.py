from rest_framework import serializers

#Local Imports
import contacts.models as cont


class MessageSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = cont.Message
		fields = ('text','translated_text','is_translated','is_pending','is_system','is_outgoing','created')

