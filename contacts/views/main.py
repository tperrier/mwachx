#Django Imports
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from jsonview.decorators import json_view
from crispy_forms.utils import render_crispy_form
from constance import config

#Python Imports
import datetime,collections,sys
import code

#Local Imports
import contacts.models as cont
import contacts.forms as forms, utils
# === Views for main action buttons ===

@login_required()
def home(request):
    
    visits = cont.Visit.objects.for_user(request.user)
    messages = cont.Message.objects.for_user(request.user)
    
    visit_count = visits.get_bookcheck().count() + visits.get_upcoming_visits().count()

    status =  {
        "messages": messages.pending().count(),
        "visits": visit_count,
        "calls": 0,
        "translations": messages.to_translate().count(),
    }
    return render(request,'home.html', {'status':status})

@login_required()
def visits(request):
    visits = cont.Visit.objects.for_user(request.user)
    visits = {
        'upcoming': visits.get_upcoming_visits(),
        'bookcheck': visits.get_bookcheck(),
    }
    return render(request,'upcoming-visits.html', {'visits':visits})

@login_required()
def calls(request):
    return render(request, 'calls-to-make.html')

@login_required()
def translations(request):
    msgs_to_translate = cont.Message.objects.for_user(request.user).to_translate()
    langs = cont.Language.objects.all()
    return render(request, 'translations.html', {'to_translate_list': msgs_to_translate, 'langs': langs})

@login_required()
def contacts(request):
    contacts = cont.Contact.objects.for_user(request.user).extra(
        select={
            'messages_sent':'select count(*) from contacts_message where contacts_message.contact_id = contacts_contact.id and contacts_message.is_outgoing = 0 and contacts_message.created < "{}"'.format(config.CURRENT_DATE),
            'messages_received':'select count(*) from contacts_message where contacts_message.contact_id = contacts_contact.id and contacts_message.is_outgoing = 1 and contacts_message.created < "{}"'.format(config.CURRENT_DATE),
        }
    )
    return render(request,'contacts/contacts.html',{'contacts':contacts})

@login_required()
def contact(request,study_id):
    try:
        contact = cont.Contact.objects.get(study_id=study_id)
    except cont.Contact.DoesNotExist as e:
        return redirect('/contact/')
    modify_form = forms.ContactModify(instance=contact)
    langs = cont.Language.objects.all()
    return render(request,'contacts/contact.html',{'contact':contact,'modify_form':modify_form, 'langs': langs})

@login_required()    
def contact_add(request):
    
    if request.POST:
        cf = forms.ContactAdd(request.POST)
        if cf.is_valid():
            #Create new contact but do not save in DB
            contact = cf.save(commit=False)
            
            #Set contacts facility to facility of current user
            facility = cont.Facility.objects.get(pk=1) #default to first facility if none found
            try:
                facility = request.user.practitioner.facility
            except cont.Practitioner.DoesNotExist:
                pass
                
            contact.facility = facility
            #Important: save before making foreign keys
            contact.save()
            
            phone_number = '+254%s'%cf.cleaned_data['phone_number'][1:]
            cont.Connection.objects.create(identity=phone_number,contact=contact,is_primary=True)

            #Send Welcome Message
            message = 'Welcome to the mWaCh X Study. Please send your five letter confirmation code'
            cont.Message.send(contact,message,'',translate_skipped=True)
            
            return redirect('contacts.views.contact',study_id=contact.study_id)
        else:
            print 'Form Error'
            print cf.errors
    else:
        cf = forms.ContactAdd()
    
    return render(request,'contacts/contact_create.html',{'form':cf})