from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', views.dashboard),
    url(r'^$', views.home),
    url(r'^message/new/?$', views.messages_new),
    url(r'^visit/$', views.visits),
    # url(r'^visit/dismiss/(?P<visit_id>\d*)/?$',views.visit_dismiss),
    url(r'^visit/dismiss/(?P<visit_id>\d*)/(?P<days>\d*)/?$',views.visit_dismiss),
    url(r'^visit/schedule/$',views.visit_schedule),
    url(r'^calls/$', views.calls),
    url(r'^translation/$', views.translations),
    url(r'^dashboard/$', views.dashboard),
    url(r'^contact/$', views.contacts),
    url(r'^contact/(?P<study_id>\d{1,3})/?$', views.contact),
    url(r'^contact/add/?$',views.contact_add),
    url(r'^contact/send/?$',views.contact_send),
    url(r'^contact/note/?$',views.add_note),
    url(r'^message/?$', views.messages),
    url(r'^message/dismiss/(?P<message_id>\d*)/?$',views.message_dismiss),
    url(r'^translation/notrequired/(?P<message_id>\d*)/?$',views.translation_not_required),
    url(r'^translation/save/(?P<message_id>\d*)/?$',views.save_translation),
)
