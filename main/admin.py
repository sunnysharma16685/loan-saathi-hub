from django.contrib import admin
from .models import User, UserProfile, AgentProfile, LoanRequest, Payment
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class CustomUserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role', 'mobile')}),
    )
    list_display = ('username', 'email', 'role', 'mobile', 'is_active')
    list_filter = ('role', 'is_active')

admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)
admin.site.register(AgentProfile)
admin.site.register(LoanRequest)
admin.site.register(Payment)
