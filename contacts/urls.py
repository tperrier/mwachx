from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
    # Examples:
    url(r'^$', views.dashboard),
    url(r'^dashboard/$', views.dashboard),
    url(r'^contact/$', views.contacts),
    url(r'^contact/(?P<study_id>\d{1,3})/$', views.contact),
    url(r'^messages/$', views.messages),
)
