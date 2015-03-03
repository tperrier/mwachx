from rest_framework import serializers

#Local Imports
import contacts.models as cont


class ParticipantSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = cont.Contact
		fields = ('nickname','study_id','study_group',)

