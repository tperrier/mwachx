from django.conf.urls import patterns, include, url
from django.contrib import admin
import contacts
from transports import http, africas_talking
from django.conf import settings

urlpatterns = patterns('',
    # Main Angular Index and Rest API
    url(r'^', include(contacts.urls)),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login',
        {'template_name': 'login.html',
         'extra_context': {'config': {'APP_NAME': getattr(settings, 'APP_NAME', 'mWaChX')}}
         }
        ),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout'),

    url(r'^message_test/',include(http.urls)),
    url(r'^africas_talking/',include(africas_talking.urls)),
)
