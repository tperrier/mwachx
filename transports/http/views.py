#!/usr/bin/python
#Django Imports
from django.shortcuts import render

#Local Imports
import contacts.models as cont
import forms


def send_message(request):

    contact = None
    system = None
    participant_send_form = forms.ParticipantSendForm()
    system_send_form = forms.SystemSendForm()
    if request.POST:
        #multiple forms on the page so check the for the send button
        if request.POST.get('participant-send',False):
            participant_send_form = forms.ParticipantSendForm(request.POST)
            if participant_send_form.is_valid():
                message = participant_send_form.save(commit=False)
                #set defaults for incoming message
                message.is_outgoing = False
                message.is_system = False
                message.connection = cont.Connection.objects.get(identity=message.contact.phone_number)
                #now save the message
                message.save()
                contact = message.contact

                #reset form on valid
                participant_send_form = forms.ParticipantSendForm()

        elif request.POST.get('system-send',False):
            system_send_form = forms.SystemSendForm(request.POST)
            if system_send_form.is_valid():
                message = system_send_form.save(commit=False)
                #set defaults for incoming message
                message.is_outgoing = True
                message.is_system = True
                message.is_viewed = True
                message.connection = cont.Connection.objects.get(identity=message.contact.phone_number)
                system = True

                message.save()
                contact = message.contact

                #reset form on valid
                system_send_form = forms.SystemSendForm()


    return render(request,'transports/http/send_message.html',
        {'participant_form':participant_send_form,'contact':contact,
          'system_form':system_send_form,'system':system})
