from django.conf import settings

import contacts.models
import datetime

def openshift(context):
	return {'ON_OPENSHIFT': settings.ON_OPENSHIFT}

def current_date(context):
	return {
		'CURRENT_DATE': settings.CURRENT_DATE,
		'ONE_WEEK': settings.CURRENT_DATE + datetime.timedelta(weeks=1)
	}

def brand_status(context):
	# do we have work to do?
	visit_count = contacts.models.Visit.objects.get_bookcheck().count() + contacts.models.Visit.objects.get_upcoming_visits().count()
	msg_count = contacts.models.Message.objects.filter(is_viewed=False).count()
	calls_count = 0 # TODO
	translation_count = 0 # TODO
	if (visit_count+msg_count+calls_count+translation_count) > 0:
		return {'BRAND_STATUS': "brand-status-danger"}
	return {'BRAND_STATUS': "brand-status-success"}
