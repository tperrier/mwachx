from django.contrib import admin

# Local Imports
import backend.models as back
# Register your models here.

@admin.register(back.AutomatedMessage)
class AutomatedMessageAdmin(admin.ModelAdmin):
    list_display = ('description','english','todo')
    list_filter = ('send_base','condition','group','todo')
