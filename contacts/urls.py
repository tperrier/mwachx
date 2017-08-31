from django.conf.urls import patterns, include, url


from serializers import router


urlpatterns = patterns('',
    # DRF API viewer
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/v0.1/', include(router.urls)),

    # Angular app
    url(r'^$', 'contacts.views.angular_view'),

    # Misc Actions
    url(r'^staff/facility_change/(?P<facility_name>.*)/$','contacts.views.staff_facility_change'), #If we have more than 9 facilities we'd need to change this
    url(r'^staff/date/(?P<direction>back|forward)/(?P<delta>\d{1,365})/$','contacts.views.change_current_date'),
    url(r'^staff/change_password/','contacts.views.change_password',name='mx-change-password'),

    # crispy-form partial
    url(r'^crispy-forms/participant/new/?$','contacts.views.crispy.participant_add'),
    url(r'^crispy-forms/participant/update/?$','contacts.views.crispy.participant_update'),
)
