#Django Imports
from django.shortcuts import render, redirect
from django.db.models import Count
from django.views.generic.edit import CreateView
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from jsonview.decorators import json_view
from crispy_forms.utils import render_crispy_form
from constance import config

#Python Imports
import datetime,collections,sys
import logging, logging.config
import code

#Local Imports
import models as cont
import forms, utils

LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO'
    }
}

logging.config.dictConfig(LOGGING)

# === Views for main action buttons ===

@json_view
def update_participant_details(request,pk=None):
    obj = get_object_or_404(cont.Contact, pk=pk)
    form = forms.ContactModify(request.POST or None, instance=obj)
    if form.is_valid():
        # You could actually save through AJAX and return a success code here
        form.save()
        return {'success': True}

    form_html = render_crispy_form(form)
    return {'success': False, 'form_html': form_html, 'errors':form.errors}

@login_required()
def home(request):
    
    visits = cont.Visit.objects.for_user(request.user)
    messages = cont.Message.objects.for_user(request.user)
    
    visit_count = visits.get_bookcheck().count() + visits.get_upcoming_visits().count()

    status =  {
        "messages": messages.filter(is_viewed=False).count(),
        "visits": visit_count,
        "calls": 0,
        "translations": messages.to_translate().count(),
    }
    return render(request,'home.html', {'status':status})

@login_required()    
def messages_new(request):
    return render(request, 'messages_new.html',{'new_message_list':cont.Message.objects.for_user(request.user).pending()})

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
            'messages_sent':'select count(*) from contacts_message where contacts_message.contact_id = contacts_contact.id and contacts_message.is_outgoing = 0',
            'messages_received':'select count(*) from contacts_message where contacts_message.contact_id = contacts_contact.id and contacts_message.is_outgoing = 1',
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
            
            cont.Connection.objects.create(identity=cf.cleaned_data['phone_number'],contact=contact,is_primary=True)
            contact.save()
            
            
            return redirect('contacts.views.contact',study_id=contact.study_id)
        else:
            print 'Form Error'
            print cf.errors
    else:
        cf = forms.ContactAdd()
    
    return render(request,'contacts/contact_create.html',{'form':cf})

# === Action views ===

# ==== Contact Page Action Views ===
@login_required()
@require_POST
def contact_send(request):
    contact = cont.Contact.objects.get(study_id=request.POST['study_id'])
    message = request.POST['message']
    parent_id = request.POST.get('parent_id',-1)
    parent = cont.Message.objects.get_or_none(pk=parent_id if parent_id else -1)
    
    #Mark Parent As Viewed If Unviewed
    if parent and parent.is_viewed == False:
        parent.is_viewed = True
        parent.save()
        
    cont.Message.send(contact,message,is_system=False,parent=parent)
    return redirect('contacts.views.contact',study_id=request.POST['study_id'])

@login_required()
def message_dismiss(request,message_id):
    message = cont.Message.objects.get(pk=message_id)
    message.is_viewed=True
    message.save()
    return redirect('contacts.views.contact',study_id=message.contact.study_id)

@login_required()
@require_POST
def add_note(request):
    contact = cont.Contact.objects.get(study_id=request.POST['study_id'])
    comment = request.POST['comment']
    cont.Note.objects.create(contact=contact,comment=comment)
    return redirect(request.META['HTTP_REFERER'])


def _record_translation(message_id, txt, langs, is_skipped=False):
    _msg = cont.Message.objects.get(id=message_id)
    lang_objs = cont.Language.objects.filter(id__in=langs)
    _msg.language_set = lang_objs

    _msg.translated_text = txt
    _msg.is_translated = True
    _msg.translate_skipped = is_skipped
    _msg.save()    

@require_POST
def save_translation(request, message_id):
    _record_translation( 
        message_id,
        request.POST['translation'],
        request.POST.getlist('languages[]'),
        is_skipped=False)

    # done, so return an http 200
    return HttpResponse()

@require_POST
def translation_not_required(request, message_id):
    _record_translation( 
        message_id,
        request.POST['translation'],
        request.POST.getlist('languages[]'),
        is_skipped=True)

    # done, so return an http 200
    return HttpResponse()
    
@require_POST
def visit_schedule(request):
    study_id = request.POST['study_id']
    # find any open visits for this client
    parent_visit = cont.Visit.objects.get_or_none(contact__study_id=study_id, arrived=None,skipped=None)

    # Mark Parent arrival time.
    if parent_visit:
        parent_visit.arrived = request.POST['arrived']
        parent_visit.save()
        
    cont.Visit.new_visit( 
        cont.Contact.objects.get(study_id=study_id),
        request.POST['next_visit'],
        request.POST['visit_type'],
        parent=parent_visit
    )
    if 'src' in request.POST.keys():
        return redirect(request.POST['src'])

    return HttpResponse()

def visit_dismiss(request,visit_id,days):
    visit = cont.Visit.objects.get(pk=visit_id)
    visit.skipped=True
    visit.comment='skipped_via_web for ' + str(days) + ' days.'
    visit.save()

    # and make a new visit
    cont.Visit.objects.create(**{
        'parent': visit.parent if visit.parent else visit,
        'scheduled': visit.scheduled,
        'contact': visit.contact,
        'reminder_last_seen': utils.today(),
        })
    return HttpResponse()
    
@staff_member_required
def staff_facility_change(request,facility_id):
    facility = cont.Facility.objects.get(pk=facility_id)
    request.user.practitioner.facility = facility
    request.user.practitioner.save()
    return HttpResponse('/') #redirect URL
    
@login_required()
def change_current_date(request,direction,delta):
    
    delta = int(delta) * (-1 if direction == 'back' else 1)
    td = datetime.timedelta(days=delta)
    config.CURRENT_DATE = utils.today() + td
    return HttpResponse('/') #redirect URL
    

# === Old Views ===
def dashboard(request):
    contacts = cont.Contact.objects.all()
    statuses = get_status_by_group()
    new_messages = cont.Message.objects.filter(is_viewed=False)
    return render(request,'dashboard.html',{'contacts':contacts,'statuses':statuses,'new_messages':new_messages})
    
def messages(request):
    messages = cont.Message.objects.all()
    contacts = cont.Contact.objects.all()
    
    grouped_messages = collections.OrderedDict()
    for m in messages:
        key = m.created.date() - datetime.timedelta(days=m.created.date().weekday())
        if key in grouped_messages:
            grouped_messages[key].append(m)
        else:
            grouped_messages[key] = [m]
    return render(request,'contacts/messages.html',{'grouped_messages':grouped_messages,'contacts':contacts})

#############
# Utility Functions
#############

def get_status_by_group():
    
    by_status = cont.Contact.objects.values('study_group','status').annotate(count=Count('study_id'))
    statuses = [ [s[1],0,0,0] for s in cont.Contact.STATUS_CHOICES ]
    
    status_map = {s[0]:i for i,s in enumerate(cont.Contact.STATUS_CHOICES) }
    group_map = {'control':1,'one-way':2,'two-way':3}
    for status in by_status:
        s_idx = status_map[status['status']]
        g_idx = group_map[status['study_group']]
        statuses[s_idx][g_idx] = status['count']
       
    #add totals
    for row in statuses:
        row.append(sum(row[1:]))
    totals = ['']
    for col in range(1,5):
        totals.append(sum([row[col] for row in statuses]))
    statuses.append(totals)
        
    return statuses
