#Django Imports
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.contrib.auth.decorators import login_required

@csrf_protect
@ensure_csrf_cookie
@login_required()
def angular_view(request):
    return render(request, 'app/index.html')
