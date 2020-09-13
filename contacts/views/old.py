#Django Imports
from django.shortcuts import render, redirect
from django.db.models import Count
from django.views.generic.edit import CreateView
from django.views.decorators.http import require_POST
from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from constance import config

#Python Imports
import datetime,collections,sys
import logging, logging.config
import code

#Local Imports
import contacts.models as cont
import utils

# === Old Views ===
def dashboard(request):
    contacts = cont.Contact.objects.all()
    statuses = get_status_by_group()
    new_messages = cont.Message.objects.filter(is_viewed=False)
    return render(request,'dashboard.html',{'contacts':contacts,'statuses':statuses,'new_messages':new_messages})

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

#############
# Static Archive Site
#############

def static_archive_index(request):
    context = {
        'participants': cont.Contact.objects.all(),
        'static_dir': '/static/static_archive/',
    }
    return render(request, 'static_archive/index.html', context)

def static_archive_participant(request, study_id):
    context = {
        'p' : cont.Contact.objects.annotate_messages().get(study_id=study_id),
        'static_dir': '/static/static_archive/',
    }
    return render(request, 'static_archive/participant.html', context)
