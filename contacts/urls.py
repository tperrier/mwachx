from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', views.dashboard),
    url(r'^$', views.home),
    url(r'^newmessages/$', views.new_messages),
    url(r'^visits/$', views.visits),
    url(r'^calls/$', views.calls),
    url(r'^translations/$', views.translations),
    url(r'^dashboard/$', views.dashboard),
    url(r'^contact/$', views.contacts),
    url(r'^contact/(?P<study_id>\d{1,3})/?$', views.contact),
    url(r'^contact/add/?$',views.contact_add),
    url(r'^contact/send/?$',views.contact_send),
    url(r'^message/?$', views.messages),
    url(r'^message/dismiss/(?P<message_id>\d*)/?$',views.message_dismiss),
)
