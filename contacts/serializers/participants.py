from rest_framework import serializers

#Local Imports
import contacts.models as cont


class ParticipantSerializer(serializers.ModelSerializer):
	# Foreign key example.
	# user = serializers.Field(source='user')

	class Meta:
		model = cont.Contact
		fields = ('nickname','study_id','study_group', 'anc_num', 'status')

