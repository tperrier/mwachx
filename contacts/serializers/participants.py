from rest_framework import serializers

#Local Imports
import contacts.models as cont


class ParticipantSerializer(serializers.ModelSerializer):
	# Foreign key example.
	# user = serializers.Field(source='user')
	status = serializers.SerializerMethodField()
	study_group = serializers.SerializerMethodField()

	class Meta:
		model = cont.Contact
		fields = ('nickname','study_id','study_group', 'anc_num', 'status')

	def get_status(self, obj):
		return obj.get_status_display()

	def get_study_group(self, obj):
		return obj.get_study_group_display()

class ParticipantDetailSerializer(serializers.ModelSerializer):
	status = serializers.SerializerMethodField()
	send_time = serializers.SerializerMethodField()
	send_day = serializers.SerializerMethodField()
	condition = serializers.SerializerMethodField()
	validation_key = serializers.SerializerMethodField()
	phone_number = serializers.SerializerMethodField()

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