from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
    # Examples:
    url(r'receive$',views.receive,name='africas-talking-receive'),
    url(r'delivery_report$',views.delivery_report,name='africas-talking-delivery-report'),
)
