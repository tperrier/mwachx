from django.conf import settings

def openshift(context):
  return {'ON_OPENSHIFT': settings.ON_OPENSHIFT}

def current_date(context):
  return {'CURRENT_DATE': settings.CURRENT_DATE}

