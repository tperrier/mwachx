from django.conf.urls import patterns, include, url
from django.contrib import admin
import contacts,http_transport,africas_talking

urlpatterns = patterns('',
    # Main Angular Index and Rest API
    url(r'^', include(contacts.urls)),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout'),

    url(r'^message_test/',include(http_transport.urls)),
    url(r'^africas_talking/',include(africas_talking.urls)),
)
