from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
    # Examples:
    url(r'^$', views.dashboard),
    url(r'^home/$', views.home),
    url(r'^dashboard/$', views.dashboard),
    url(r'^contact/$', views.contacts),
    url(r'^contact/(?P<study_id>\d{1,3})/$', views.contact),
    url(r'^contact/add/?',views.contact_add),
    url(r'^contact/send/?',views.contact_send),
    url(r'^messages/$', views.messages),
)
