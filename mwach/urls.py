from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views
import contacts.urls as contacts_urls
from transports import http, africas_talking

urlpatterns = [
    # Main Angular Index and Rest API
    url(r'^', include(contacts_urls)),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', auth_views.login, {'template_name': 'login.html'}),
    url(r'^accounts/logout/$', auth_views.logout),
    url(r'^message_test/',include(http.urls)),
    url(r'^africas_talking/',include(africas_talking.urls)),
]
