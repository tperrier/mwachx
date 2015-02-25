#Django Imports
from django.views.generic.edit import FormView
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

#Local Imports
import forms
from contacts.models import Message


@csrf_exmpt
def receive(request):
	
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
	return render(request,'africas_talking/test_receive.html',{'form':form})

