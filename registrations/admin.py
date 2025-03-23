from django.contrib import admin

# Register your models here.
from .models import Registration, FormResponse, EmailCommunication

class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'status', 'registration_date')
    list_filter = ('status', 'event')
    search_fields = ('name', 'email', 'event__name')


admin.site.register(Registration, RegistrationAdmin)
admin.site.register(FormResponse)
admin.site.register(EmailCommunication)