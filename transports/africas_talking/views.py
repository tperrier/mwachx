#Python Import
import logging

#Django Imports
from django.views.generic.edit import FormView
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

#Local Imports
import forms
from contacts.models import Message


# Get an instance of a logger
logger = logging.getLogger(__name__)


@csrf_exempt
def receive(request):

	logger.debug('receive(): %s\n%s\n%s',request.method,request.META,request.POST)

	if request.method == 'POST':
		form = forms.AfricasTalkingForm(request.POST)
		if form.is_valid():
			Message.receive(**{
				'number':form.cleaned_data['from'],
				'message':form.cleaned_data['text'],
				'time_received':form.cleaned_data['date'],
				'external_id':form.cleaned_data['id'],
				'external_linkId':form.cleaned_data['linkId'],
			})
			return render(request,'africas_talking/test_receive.html',{'form':form})
	else: #GET request
		form = forms.AfricasTalkingForm()
	return render(request,'transports/africas_talking/test_receive.html',{'form':form})
