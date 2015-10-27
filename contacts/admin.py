from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

#Local Imports
import models as cont

@admin.register(cont.Contact)
class ContactAdmin(admin.ModelAdmin):

    list_display = ('study_id','nickname','study_group','status','due_date','facility')
    list_filter = ('study_group','status','facility')

    date_hierarchy = 'due_date'
    ordering = ('study_id',)

    search_fields = ('^study_id','^nickname')
    readonly_fields = ('created','modified')

@admin.register(cont.Message)
class MessageAdmin(admin.ModelAdmin):

    list_display = ('text','contact_name','is_viewed','is_system','is_outgoing','languages',
        'translated_text','translation_status','is_related','identity',
        'external_id','external_linkId','time_received','created')
    date_hierarchy = 'created'
    list_filter = ('is_viewed','is_system','is_outgoing','translation_status')
    search_fields = ('^contact__study_id','^contact__first_name','^contact__last_name')

@admin.register(cont.PhoneCall)
class PhoneCallAdmin(admin.ModelAdmin):

    list_display = ('created','contact','outcome','is_outgoing','comment')

@admin.register(cont.Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('identity','contact')

@admin.register(cont.Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('study_id','participant_name','visit_type','scheduled', 'notification_last_seen','notify_count', 'arrived','skipped')
    list_filter = ('skipped','visit_type')

@admin.register(cont.ScheduledPhoneCall)
class ScheduledPhoneCall(admin.ModelAdmin):
    list_display = ('study_id','participant_name','call_type','scheduled', 'notification_last_seen','notify_count', 'arrived','skipped')
    list_filter = ('skipped','call_type')

@admin.register(cont.Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('pk','__str__')

@admin.register(cont.Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = ('facility','username')

class PractitionerInline(admin.TabularInline):
    model = cont.Practitioner

class UserAdmin(UserAdmin):
    inlines = (PractitionerInline,)

#Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User,UserAdmin)
