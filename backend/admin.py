from django.contrib import admin

# Local Imports
import backend.models as back
# Register your models here.

@admin.register(back.Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('pk','__str__')
    list_display_links = ('pk','__str__')
