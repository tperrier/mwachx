#Django Imports
from django.shortcuts import render, redirect
from django.db.models import Count

#Local Imports
import models as cont


def dashboard(request):
    contacts = cont.Contact.objects.all()
    statuses = get_status_by_group()
    return render(request,'dashboard.html',{'contacts':contacts,'statuses':statuses})
    
def messages(request):
    messages = cont.Message.objects.all()
    contacts = cont.Contact.objects.all()
    return render(request,'messages.html',{'messages':messages,'contacts':contacts})
    
def contacts(request):
    contacts = cont.Contact.objects.all()
    return render(request,'contacts.html',{'contacts':contacts})
    
def contact(request,study_id):
    try:
        contact = cont.Contact.objects.get(study_id=study_id)
    except cont.Contact.DoesNotExist as e:
        return redirect('/contact/')
    contacts = cont.Contact.objects.all()
    return render(request,'contact.html',{'contact':contact,'contacts':contacts})

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
        
    return statuses
