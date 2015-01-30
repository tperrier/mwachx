#Django Imports
from django.shortcuts import render, redirect
from django.db.models import Count
from django.views.generic.edit import CreateView
from django.views.decorators.http import require_POST

#Python Imports
import datetime,collections
import code

#Local Imports
import models as cont
import forms


def home(request):
    status =  {
        "messages": 5,
        "visits": 3,
        "calls": 0,
        "translations": 1,
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
    contacts = cont.Contact.objects.all()
    return render(request,'contacts/contact.html',{'contact':contact,'contacts':contacts})

@require_POST
def contact_send(request):
    print request.POST
    contact = cont.Contact.objects.get(study_id=request.POST['study_id'])
    message = request.POST['message']
    cont.Message.send(contact,message,is_system=False)
    return redirect('contacts.views.contact',study_id=request.POST['study_id'])
    
    
def contact_add(request):
    
    if request.POST:
        cf = forms.ContactAdd(request.POST)
        if cf.is_valid():
            print 'valid'
            #Create new contact but do not save in DB
            contact = cf.save(commit=False)
            contact.save()
            cont.Connection.objects.create(identity=cf.cleaned_data['phone_number'],contact=contact,is_primary=True)
            return redirect('contacts.views.contact',study_id=contact.study_id)
    else:
        cf = forms.ContactAdd()
        
    fieldsets = {
        'Study Information':[cf['study_id'],cf['anc_num'],cf['study_group'],cf['send_day'],cf['send_time']],
        'Client Information':[cf['nickname'],cf['phone_number'],cf['birthdate'],cf['partner_name'],
                              cf['relationship_status'],cf['previous_pregnancies'],cf['language']],
        'Medical Information':[cf['condition'],cf['art_initiation'],cf['due_date']],
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
