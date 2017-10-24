#Django Imports
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.conf import settings
from constance import config

@csrf_protect
@ensure_csrf_cookie
@login_required()
def angular_view(request):
    FAKE_DATE = getattr(settings,'FAKE_DATE', True)
    return render(request, 'app/index.html', context={'config': {
        'SHOW_DATE':FAKE_DATE,
        'SHOW_VISITS':config.SHOW_VISITS,
        'user':request.user
        }})
