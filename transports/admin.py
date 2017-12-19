from django.contrib import admin

# Local Imports
import transports.models as trans
# Register your models here.

@admin.register(trans.ForwardMessage)
class ForwardMessageAdmin(admin.ModelAdmin):
    list_display = ('created','identity','text','fwrd_status','transport','url')
    list_filter = ('fwrd_status','transport')
    readonly_fields = ('created','modified')
