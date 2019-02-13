from django.conf.urls import include, url
import views

urlpatterns = [
    # Examples:
    url(r'receive$',views.receive,name='africas-talking-receive'),
    url(r'delivery_report$',views.delivery_report,name='africas-talking-delivery-report'),
]
