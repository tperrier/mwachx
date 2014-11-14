from django.conf.urls import patterns, include, url
from django.contrib import admin
import contacts

urlpatterns = patterns('',
    # Examples:
    url(r'^', include(contacts.urls)),
    url(r'^admin/', include(admin.site.urls)),
)
