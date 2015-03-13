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

    # crispy-form partial
    url(r'^crispy-forms/participant/new/?$','contacts.views.generate_add_participant_form'),
)
