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
	nonzero = 0
	if contacts.models.Visit.objects.get_bookcheck().count() + contacts.models.Visit.objects.get_upcoming_visits().count() > 0: nonzero = nonzero + 1
	if contacts.models.Message.objects.filter(is_viewed=False).count() > 0: nonzero = nonzero + 1
	if 0 > 0: nonzero = nonzero + 1
	if 0 > 0: nonzero = nonzero + 1

	if nonzero > 0:
		# if nonzero == 1:
		# 	return {'BRAND_STATUS': "brand-status-warning"}	
		return {'BRAND_STATUS': "brand-status-danger"}
	return {'BRAND_STATUS': "brand-status-success"}
