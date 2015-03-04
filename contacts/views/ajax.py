#Django Imports
from django.shortcuts import render, redirect
from django.db.models import Count
from django.views.generic.edit import CreateView
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from jsonview.decorators import json_view
from constance import config

#Python Imports
import datetime,collections,sys
import code
import json

#Local Imports
import contacts.models as cont
import contacts.forms as forms, utils





@csrf_protect
@ensure_csrf_cookie
@login_required()
def participant_view(request):
    return render(request, 'app/participant.html')








# === Action views ===

#TODO: No CSRF protection yet. (let's use PUT and the REST plugin)
@json_view
def message_update(request,message_id=None):
    msg = get_object_or_404(cont.Message, pk=message_id)
    if not request.POST:
        return HttpResponseBadRequest()
    
    if 'is_translated' in request.POST.keys(): msg.is_translated = (request.POST['is_translated'].lower() in ('true'))
    if 'translate_skipped' in request.POST.keys(): msg.translate_skipped = (request.POST['translate_skipped'].lower() in ('true'))
    y = msg.is_translated
    msg.save()
    msg = get_object_or_404(cont.Message, pk=message_id)
    x = msg.is_translated
    return {'success': x, 'pre': y}

# TODO: No CSRF protection yet. (let's use PUT and the REST plugin)
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
def messages_new(request):
    return render(request, 'messages_new.html',{'new_message_list':cont.Message.objects.for_user(request.user).pending()})

# ==== Contact Page Action Views ===
@login_required()
@require_POST
def contact_send(request):
    contact = cont.Contact.objects.get(study_id=request.POST['study_id'])
    message = request.POST['message']
    translation = request.POST['translation']
    parent_id = request.POST.get('parent_id',-1)
    parent = cont.Message.objects.get_or_none(pk=parent_id if parent_id else -1)
    
    is_translated = json.loads(request.POST["is_translated"]) if "is_translated" in request.POST.keys() else False
    translate_skipped = json.loads(request.POST["translate_skipped"]) if "translate_skipped" in request.POST.keys() else False
    #Mark Parent As Viewed If Unviewed
    if parent and parent.is_viewed == False:
        parent.is_related = request.POST['relatedToggle']
        parent.topic = request.POST['topic']
        parent.is_viewed = True
        parent.save()
    
    cont.Message.send(contact,message,translation,
        languages=request.POST.getlist('language'),
        is_translated=is_translated,
        translate_skipped=translate_skipped,
        is_system=False,parent=parent)
    return redirect('contacts.views.contact',study_id=request.POST['study_id'])

@login_required()
@require_POST
def message_dismiss(request,message_id):
    message = cont.Message.objects.get(pk=message_id)
    langs = request.POST.getlist('parent-language') # If posted from a form, don't use []'s
    lang_objs = cont.Language.objects.filter(id__in=langs)
    message.languages = lang_objs
    message.topic = request.POST['topic']
    message.is_related = json.loads(request.POST['relatedToggle'])
    message.is_viewed = True
    message.save()
    return redirect('contacts.views.messages_new')

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
    _msg.languages = lang_objs

    _msg.translated_text = txt
    _msg.is_translated = True
    _msg.translate_skipped = is_skipped
    _msg.save()    

@require_POST
def save_translation(request, message_id):
    _record_translation( 
        message_id,
        request.POST['translation'],
        request.POST.getlist('languages[]'), # if posted from jquery, need the []'s. See: http://stackoverflow.com/questions/11190070/django-getlist
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
        parent_visit.arrived = utils.parse_date(request.POST['arrived'])
        parent_visit.save()
        
    cont.Visit.objects.create(**{
        'contact':cont.Contact.objects.get(study_id=study_id),
        'scheduled':utils.parse_date(request.POST['next_visit']),
        'visit_type':request.POST['visit_type'],
        'parent':parent_visit,
    })
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