from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, AgentProfile, LoanRequest, Payment


class CustomUserAdmin(BaseUserAdmin):
    # username ke jagah email/mobile ka use
    ordering = ("email",)
    list_display = ("email", "mobile", "role", "is_active")
    list_filter = ("role", "is_active", "is_staff")

    # jo fields admin panel me dikhengi (update ke liye)
    fieldsets = (
        (None, {"fields": ("email", "mobile", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Role", {"fields": ("role",)}),
    )

    # user add karte waqt admin panel me jo fields dikhengi
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "mobile", "role", "password1", "password2"),
        }),
    )

    search_fields = ("email", "mobile")


# models ko register karo
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)
admin.site.register(AgentProfile)
admin.site.register(LoanRequest)
admin.site.register(Payment)

