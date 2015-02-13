#Django Imports
from django.shortcuts import render, redirect
from django.db.models import Count
from django.views.generic.edit import CreateView
from django.views.decorators.http import require_POST
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponseBadRequest, HttpResponse

#Python Imports
import datetime,collections
import code

#Local Imports
import models as cont
import forms

import logging, logging.config
import sys

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


def translations(request):
    msgs_to_translate = cont.Message.objects.filter(is_system=False).filter(Q(translation=None)|Q(translation__is_complete=False))
    langs = cont.Language.objects.all()
    return render(request, 'translations.html', {'to_translate_list': msgs_to_translate, 'langs': langs})

def calls(request):
    return render(request, 'calls-to-make.html')


def record_translation(message_id, txt, langs, is_skipped=False):
    _msg = cont.Message.objects.get(id=message_id)
    lang_objs = cont.Language.objects.filter(id__in=langs)
    _msg.language_set = lang_objs

    if(_msg.translation):
        _msg.translation.text = txt
        _msg.translation.is_complete = True
        _msg.translation.is_skipped = is_skipped
        _msg.translation.save()
    else:
        new_translation = {
            'text':txt,
            'is_complete':True,
            'is_skipped':is_skipped,
            'parent': cont.Message.objects.get(id=message_id),
        }
        _trans = cont.Translation.objects.create(**new_translation)
        _msg.translation = _trans
    

    # done, so return an http 200
    _msg.save()
    return HttpResponse()    
    

@require_POST
def translation_not_required(request, message_id):

    record_translation( 
        message_id,
        request.POST['translation'],
        request.POST.getlist('languages[]'),
        is_skipped=True)

    return HttpResponse()
    # return HttpResponseBadRequest()
    # return redirect('contacts.views.visits')

@require_POST
def visit_schedule(request):
    next_visit = request.POST['next_visit']
    arrived = request.POST['arrived']
    study_id = request.POST['study_id']
    contact = cont.Contact.objects.get(study_id=study_id)

    # find any open visits for this client
    parent_visit = cont.Visit.objects.get_or_none(contact__study_id=study_id, arrived=None,skipped=None)
    original_scheduled = next_visit

    # Mark Parent arrival time.
    if parent_visit:
        parent_visit.arrived = arrived
        parent_visit.save()
        original_scheduled = parent_visit.original_scheduled
        
    cont.Visit.new_visit(contact,next_visit,original_scheduled,parent=parent_visit)
    return redirect(request.POST['src'])

def visit_dismiss(request,visit_id,days):
    today = settings.CURRENT_DATE
    visit = cont.Visit.objects.get(pk=visit_id)
    visit.skipped=True
    visit.comment='skipped_via_web for ' + str(days) + ' days.'
    visit.save()

    # and make a new visit
    cont.Visit.objects.create(**{
        'parent': visit.parent if visit.parent else visit,
        'scheduled': visit.scheduled,
        'contact': visit.contact,
        'reminder_last_seen': today,
        })
    return redirect('contacts.views.visits')
    


def visits(request):
    visits = {
        'upcoming': cont.Visit.objects.get_upcoming_visits(),
        'bookcheck': cont.Visit.objects.get_bookcheck(),
    }
    return render(request,'upcoming-visits.html', {'visits':visits})

def home(request):
    visit_count = cont.Visit.objects.get_bookcheck().count() + cont.Visit.objects.get_upcoming_visits().count()

    status =  {
        "messages": cont.Message.objects.filter(is_viewed=False).count(),
        "visits": visit_count,
        "calls": 0,
        "translations": cont.Message.objects.filter(Q(translation=None)|Q(translation__is_complete=False)).count(),
    }
    return render(request,'home.html', {'status':status})

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
    
def contacts(request):
    contacts = cont.Contact.objects.all().extra(
        select={
            'messages_sent':'select count(*) from contacts_message where contacts_message.contact_id = contacts_contact.id and contacts_message.is_outgoing = 0',
            'messages_received':'select count(*) from contacts_message where contacts_message.contact_id = contacts_contact.id and contacts_message.is_outgoing = 1',
        }
    )
    return render(request,'contacts/contacts.html',{'contacts':contacts})
    
def contact(request,study_id):
    try:
        contact = cont.Contact.objects.get(study_id=study_id)
    except cont.Contact.DoesNotExist as e:
        return redirect('/contact/')
    modify_form = forms.ContactModify(instance=contact)
    return render(request,'contacts/contact.html',{'contact':contact,'modify_form':modify_form})

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
    
def message_dismiss(request,message_id):
    message = cont.Message.objects.get(pk=message_id)
    message.is_viewed=True
    message.save()
    return redirect('contacts.views.contact',study_id=message.contact.study_id)
    
@require_POST
def add_note(request):
    contact = cont.Contact.objects.get(study_id=request.POST['study_id'])
    comment = request.POST['comment']
    cont.Note.objects.create(contact=contact,comment=comment)
    return redirect(request.META['HTTP_REFERER'])

def messages_new(request):
    return render(request, 'messages_new.html',{'new_message_list':cont.Message.objects.pending()})
    
def contact_add(request):
    
    if request.POST:
        cf = forms.ContactAdd(request.POST)
        if cf.is_valid():
            #Create new contact but do not save in DB
            contact = cf.save(commit=False)
            
            cont.Connection.objects.create(identity=to,contact=contact,is_primary=True)
            contact.save()
            
            
            return redirect('contacts.views.contact',study_id=contact.study_id)
        else:
            print 'Form Error'
    else:
        cf = forms.ContactAdd()
        
    fieldsets = {
        'Study Information':[cf['study_id'],cf['anc_num'],cf['study_group'],cf['send_day'],cf['send_time']],
        'Client Information':[cf['nickname'],cf['phone_number'],cf['birthdate'],cf['partner_name'],
                              cf['relationship_status'],cf['previous_pregnancies'],cf['language']],
        'Medical Information':[cf['condition'],cf['art_initiation'],cf['hiv_disclosed'],cf['due_date']],
    }
    
    return render(request,'contacts/contact_create.html',{'fieldsets':fieldsets})

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
