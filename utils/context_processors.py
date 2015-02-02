from django.conf import settings
import datetime

def openshift(context):
	return {'ON_OPENSHIFT': settings.ON_OPENSHIFT}

def current_date(context):
	return {
		'CURRENT_DATE': settings.CURRENT_DATE,
		'ONE_WEEK': settings.CURRENT_DATE + datetime.timedelta(weeks=1)
	}

