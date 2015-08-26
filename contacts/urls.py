from django.conf.urls import patterns, include, url

from rest_framework import routers

import views
from views import api
# from views import angular_views

router = routers.DefaultRouter()
router.register(r'v0.1/participant', api.ParticipantViewSet, 'Participant')
router.register(r'v0.1/message',     api.MessageViewSet,     'Message')


urlpatterns = patterns('',
    # DRF API viewer
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/', include(router.urls)),

    # Angular app
    url(r'^$', 'contacts.views.angular_view'),
    # Examples:
    # url(r'^$', 'contacts.views.dashboard'),
    # url(r'^$', 'contacts.views.home'),
    url(r'^message/new/?$', 'contacts.views.messages_new'),
    url(r'^visit/$', 'contacts.views.visits'),
    # url(r'^visit/dismiss/(?P<visit_id>\d*)/?$','contacts.views.visit_dismiss'),
    url(r'^visit/dismiss/(?P<visit_id>\d*)/(?P<days>\d*)/?$','contacts.views.visit_dismiss'),
    url(r'^visit/schedule/$','contacts.views.visit_schedule'),
    url(r'^calls/$', 'contacts.views.calls'),
    url(r'^translation/$', 'contacts.views.translations'),
    url(r'^dashboard/$', 'contacts.views.dashboard'),
    url(r'^contact/$', 'contacts.views.contacts'),
    url(r'^contact/(?P<study_id>\d*)/?$', 'contacts.views.contact'),
    url(r'^contact/add/?$','contacts.views.contact_add'),
    url(r'^contact/send/?$','contacts.views.contact_send'),
    url(r'^contact/note/?$','contacts.views.add_note'),
    url(r'^message/?$', 'contacts.views.messages'),
    url(r'^message/update/(?P<message_id>\d*)/?$','contacts.views.message_update'),
    url(r'^message/dismiss/(?P<message_id>\d*)/?$','contacts.views.message_dismiss'),
    
    url(r'^staff/facility_change/(?P<facility_name>.*)/$','contacts.views.staff_facility_change'), #If we have more than 9 facilities we'd need to change this
    url(r'^staff/date/(?P<direction>back|forward)/(?P<delta>\d{1,365})/$','contacts.views.change_current_date'),

    # crispy-form partial
    url(r'^crispy-forms/participant/new/?$','contacts.views.generate_add_participant_form'),
)
