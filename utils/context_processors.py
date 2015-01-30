from django.conf import settings

def openshift(context):
  return {'ON_OPENSHIFT': settings.ON_OPENSHIFT}
