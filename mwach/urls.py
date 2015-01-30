from django.conf.urls import patterns, include, url
from django.contrib import admin
import contacts,http_transport

urlpatterns = patterns('',
    # Examples:
    url(r'^', include(contacts.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^message_test/',include(http_transport.urls)),
)
