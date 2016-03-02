from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils import html

#Local Imports
import models as cont

class ConnectionInline(admin.TabularInline):
    model = cont.Connection
    extra = 0

@admin.register(cont.Contact)
class ContactAdmin(admin.ModelAdmin):

    list_display = ('study_id','nickname','status','description','facility',
        'phone_number','due_date','language','send_day','is_validated','created')
    list_display_links = ('study_id','nickname')
    list_filter = ('facility','study_group', ('created',admin.DateFieldListFilter), 'hiv_messaging','status','is_validated','language','send_day')

    ordering = ('study_id',)

    search_fields = ('study_id','nickname','connection__identity','anc_num')
    readonly_fields = ('last_msg_client','last_msg_system','created','modified')

    inlines = (ConnectionInline,)

def ParticipantMixinFactory(field='participant'):
    class ParticipantAdminMixinBase(object):

        participant_field = field

        def participant_name(self,obj):
            participant = getattr(obj,self.participant_field)
            if participant is not None:
                return html.format_html("<a href='../contact/{0.pk}'>({0.study_id}) {0.nickname}</a>".format(participant) )
        participant_name.short_description = 'Nickname'
        participant_name.admin_order_field = '{}__study_id'.format(participant_field)

        def facility(self,obj):
            participant = getattr(obj,self.participant_field)
            if participant is not None:
                return participant.facility.capitalize()
        facility.admin_order_field = '{}__facility'.format(participant_field)

        def study_id(self,obj):
            return getattr(obj,self.participant_field).study_id
        study_id.short_description = 'Study ID'
        study_id.admin_order_field = '{}__study_id'.format(participant_field)

        def phone_number(self,obj):
            connection = getattr(obj,self.participant_field).connection()
            if connection is not None:
                return html.format_html("<a href='../connection/{0.pk}'>{0.identity}</a>".format(connection) )
        phone_number.short_description = 'Number'
        phone_number.admin_order_field = '{}__connection__identity'.format(participant_field)

    return ParticipantAdminMixinBase

ParticipantAdminMixin = ParticipantMixinFactory()
ContactAdminMixin = ParticipantMixinFactory('contact')

@admin.register(cont.Message)
class MessageAdmin(admin.ModelAdmin,ContactAdminMixin):

    list_display = ('text','participant_name','identity','is_viewed','is_system',
        'is_outgoing', 'is_reply', 'translation_status','external_success','created')
    list_filter = ('is_viewed','is_system','is_outgoing', ('created', admin.DateFieldListFilter) ,'connection__contact__facility',
    'translation_status','is_related')

    search_fields = ('contact__study_id','contact__nickname','connection__identity')
    readonly_fields = ('created','modified')

    def identity(self,obj):
        return html.format_html("<a href='../connection/{0.pk}'>{0.identity}</a>".format(
            obj.connection
        ) )
    identity.short_description = 'Number'
    identity.admin_order_field = 'connection__identity'

@admin.register(cont.PhoneCall)
class PhoneCallAdmin(admin.ModelAdmin):

    list_display = ('comment','contact_name','outcome','is_outgoing','created')
    date_hierarchy = 'created'
    list_filter = ('outcome','is_outgoing')
    readonly_fields = ('created','modified')

@admin.register(cont.Connection)
class ConnectionAdmin(admin.ModelAdmin,ContactAdminMixin):
    list_display = ('identity','participant_name','facility','is_primary')
    search_fields = ('contact__study_id','contact__nickname','identity')


@admin.register(cont.Visit)
class VisitAdmin(admin.ModelAdmin,ParticipantAdminMixin):
    list_display = ('study_id','participant_name','visit_type','scheduled',
        'notification_last_seen','notify_count', 'arrived','status')
    date_hierarchy = 'scheduled'
    list_filter = ('status','visit_type','arrived','scheduled')
    search_fields = ('participant__study_id','participant__nickname')

@admin.register(cont.ScheduledPhoneCall)
class ScheduledPhoneCall(admin.ModelAdmin,ParticipantAdminMixin):
    list_display = ('study_id','participant_name','call_type','scheduled',
        'notification_last_seen','notify_count', 'arrived','status')
    date_hierarchy = 'scheduled'
    list_filter = ('status','call_type','arrived','scheduled')

@admin.register(cont.Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = ('facility','username','password_changed')

@admin.register(cont.StatusChange)
class StatusChangeAdmin(admin.ModelAdmin,ContactAdminMixin):
    list_display = ('comment','participant_name','old','new','type','created')

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
