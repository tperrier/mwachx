#Django Imports
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from crispy_forms.utils import render_crispy_form
from constance import config

#Python Imports
import datetime,collections,sys
import code

#Local Imports
import contacts.models as cont
import contacts.forms as forms
import utils
# === Views for main action buttons ===


@login_required()
def participant_add(request):
    cf = forms.ContactAdd()
    return render(request,'crispy/generic.html',{'form':cf,'form_name':'participant-create-form'})

@login_required()
def participant_update(request):
    cf = forms.ContactUpdate()
    return render(request,'crispy/generic.html',{'form':cf,'form_name':'participant-update-form'})
