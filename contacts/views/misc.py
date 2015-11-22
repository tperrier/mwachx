#Django Imports
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from constance import config

#Python Imports
import datetime

#Local Imports
import contacts.models as cont
import backend.models as back
import utils


@staff_member_required
def staff_facility_change(request,facility_name):
    request.user.practitioner.facility = facility_name
    request.user.practitioner.save()
    return JsonResponse({'current_facility':facility_name})

@login_required()
def change_current_date(request,direction,delta):

    delta = int(delta) * (-1 if direction == 'back' else 1)
    td = datetime.timedelta(days=delta)
    config.CURRENT_DATE = utils.today() + td
    return JsonResponse({'current_date':config.CURRENT_DATE.strftime('%Y-%m-%d')})
