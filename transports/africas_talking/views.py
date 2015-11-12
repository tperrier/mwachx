#Python Import
import logging

#Django Imports
from django.views.generic.edit import FormView
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

#Local Imports
import forms
from contacts.models import Message
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
				message=form.cleaned_data['text'],
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
