from django.contrib import admin

#Local Imports
import models as cont

@admin.register(cont.Contact)
class ContactAdmin(admin.ModelAdmin):
    
    list_display = ('study_id','first_name','last_name','study_group','status','due_date')
    list_filter = ('study_group','status')
    
    date_hierarchy = 'due_date'
    ordering = ('study_id',)
    
    search_fields = ('^study_id','^first_name','^last_name')
    
@admin.register(cont.Message)
class MessageAdmin(admin.ModelAdmin):
    
    list_display = ('study_id','first_name','last_name','study_group','identity','text','created')
    date_hierarchy = 'created'
    
    search_fields = ('^contact__study_id','^contact__first_name','^contact__last_name')
    
@admin.register(cont.Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ('identity','contact')
    
