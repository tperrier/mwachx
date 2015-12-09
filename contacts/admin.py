from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

#Local Imports
import models as cont

@admin.register(cont.Contact)
class ContactAdmin(admin.ModelAdmin):

    list_display = ('study_id','nickname','study_group','status','due_date','facility',
        'send_day','send_time','is_validated')
    list_display_links = ('study_id','nickname')
    list_filter = ('study_group','status','facility','send_day','is_validated')

    date_hierarchy = 'due_date'
    ordering = ('study_id',)

    search_fields = ('^study_id','^nickname')
    readonly_fields = ('created','modified')

@admin.register(cont.Message)
class MessageAdmin(admin.ModelAdmin):

    list_display = ('text','contact_name','is_viewed','is_system','is_outgoing','languages',
        'translation_status', 'external_id','external_success','external_data')
    date_hierarchy = 'created'
    list_filter = ('is_viewed','is_system','is_outgoing','translation_status','is_related')
    search_fields = ('^contact__study_id','^contact__first_name','^contact__last_name')

    readonly_fields = ('created','modified')

@admin.register(cont.PhoneCall)
class PhoneCallAdmin(admin.ModelAdmin):

    list_display = ('comment','contact_name','outcome','is_outgoing','created')
    date_hierarchy = 'created'
    list_filter = ('outcome','is_outgoing')
    readonly_fields = ('created','modified')

@admin.register(cont.Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('identity','contact')

class ScheduledEventAdmin(admin.ModelAdmin):

    def participant_name(self,obj):
        return '<a href="../contact/{0.study_id}">{0.nickname}</a>'.format(obj.participant)
    participant_name.short_description = 'Nickname'
    participant_name.admin_order_field = 'participant__nickname'
    participant_name.allow_tags = True

    def study_id(self,obj):
        return obj.participant.study_id
    study_id.short_description = 'Study ID'
    study_id.admin_order_field = 'contact__study_id'

@admin.register(cont.Visit)
class VisitAdmin(ScheduledEventAdmin):
    list_display = ('study_id','participant_name','visit_type','scheduled',
        'notification_last_seen','notify_count', 'arrived','skipped')
    date_hierarchy = 'arrived'
    list_filter = ('skipped','visit_type')
    search_fields = ('participant__study_id','^participant__nickname')

@admin.register(cont.ScheduledPhoneCall)
class ScheduledPhoneCall(ScheduledEventAdmin):
    list_display = ('study_id','participant_name','call_type','scheduled', 'notification_last_seen','notify_count', 'arrived','skipped')
    list_filter = ('skipped','call_type')

@admin.register(cont.Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = ('facility','username')

@admin.register(cont.StatusChange)
class StatusChangeAdmin(ScheduledEventAdmin):
    list_display = ('comment','contact_name','old','new','type','created')

@admin.register(cont.EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ('user','event','created')

class PractitionerInline(admin.TabularInline):
    model = cont.Practitioner

class UserAdmin(UserAdmin):
    inlines = (PractitionerInline,)

#Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User,UserAdmin)
