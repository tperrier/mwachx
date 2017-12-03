#Python Import
import logging
import os
import requests

#Django Imports
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings

#Local Imports
import forms
import contacts.models as cont
import transports


# Get an instance of a logger
logger = logging.getLogger(__name__)


@csrf_exempt
def receive(request):

	logger.debug('receive(): %s\n%s\n%s',request.method,request.META,request.POST)

	if request.method == 'POST' and can_submit(request):
		form = forms.AfricasTalkingForm(request.POST)
		if form.is_valid():
			message = transports.receive(
				identity=form.cleaned_data['from'],
				message_text=form.cleaned_data['text'],
				external_id=form.cleaned_data['id'],
				time_received=form.cleaned_data['date'],
				external_linkId=form.cleaned_data['linkId']
			)
			return render(request,'transports/africas_talking/test_receive.html',{'form':form})
	else: #GET request
		form = forms.AfricasTalkingForm()
	return render(request,'transports/africas_talking/test_receive.html',{'form':form})

def can_submit(request):
	if request.POST.has_key('web_token'):
		return request.user.is_authenticated()
	return True

@csrf_exempt
def delivery_report(request):

	if request.method == 'POST':
		status = request.POST['status']
		message_id = request.POST['id']
		failure_reason = request.POST.get('failureReason')

		try:
			message = cont.Message.objects.get(external_id=message_id)
		except cont.Message.DoesNotExist as e:
			# message for ID does not exist forward delivery report if needed

			sms_forward_base_url = getattr(settings,'SMS_FORWARD_BASE_URL',None)
			if sms_forward_base_url is not None:
				sms_forward_url = os.path.join(sms_forward_base_url,'africas_talking','delivery_report')
				params = {'status':status,'id':message_id,'failureReason':failure_reason}
				try:
					post = requests.post(sms_forward_url,data=params)
					output = post.text
				except requests.exceptions.RequestException as e:
					return HttpResponse("FORWARD URL FAILED")
			else:
				return HttpResponse("NO MESSAGE FOR ID FOUND")
		else:
			message.external_status = status
			message.external_success_time = timezone.now()
			if failure_reason is not None:
				message.external_data['reason'] = failure_reason
			message.save()
			output = "{} , {} , {}\n".format( status , message_id , failure_reason )

		return HttpResponse(output)
	else:
		return HttpResponse("HTTP POST REQUIRED")
