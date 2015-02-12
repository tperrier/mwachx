from django.contrib import admin

#Local Imports
import models as cont

@admin.register(cont.Contact)
class ContactAdmin(admin.ModelAdmin):
    
    list_display = ('study_id','nickname','study_group','status','due_date','facility')
    list_filter = ('study_group','status','facility')
    
    date_hierarchy = 'due_date'
    ordering = ('study_id',)
    
    search_fields = ('^study_id','^nickname',)
    
@admin.register(cont.Message)
class MessageAdmin(admin.ModelAdmin):
    
    list_display = ('study_id','is_viewed','is_system','is_outgoing','contact_name','translation','identity','text','created')
    date_hierarchy = 'created'
    list_filter = ('is_viewed','is_system','is_outgoing')
    search_fields = ('^contact__study_id','^contact__first_name','^contact__last_name')

@admin.register(cont.Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ('parent','text','is_complete','is_skipped')
    
@admin.register(cont.Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('identity','contact')
    
@admin.register(cont.Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('study_id','parent','contact_name','scheduled', 'reminder_last_seen', 'arrived','skipped')
    date_hierarchy = 'scheduled'
    list_filter = ('skipped',)
    
@admin.register(cont.Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('pk','name')
    
