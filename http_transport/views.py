#!/usr/bin/python
#Django Imports
from django.shortcuts import render

#Local Imports
import contacts.models as cont
import forms


def send_message(request):
    
    contact = None
    message_send_form = forms.MessageSendForm()
    if request.POST:
        message_send_form = forms.MessageSendForm(request.POST)
        
        if message_send_form.is_valid():
            message = message_send_form.save(commit=False)
            #set defaults for incomming message
            message.is_outgoing = False
            message.is_system = False
            message.connection = cont.Connection.objects.get(identity=message.contact.phone_number)
            #now save the message
            message.save()
            contact = message.contact
            
            #reset form on valid
            message_send_form = forms.MessageSendForm()
            
    
    
    return render(request,'http_transport/send_message.html',{'form':message_send_form,'contact':contact})
