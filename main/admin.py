from django.contrib import admin
from .models import PageAd

from .models import (
    User,
    Profile,
    ApplicantDetails,
    LenderDetails,
    LoanRequest,
    PaymentTransaction,
)


# ------------------ Custom Admin Classes ------------------

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("user_id", "email", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("email", "user_id")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "mobile", "pancard_number", "aadhaar_number", "city", "state")
    search_fields = ("full_name", "mobile", "pancard_number", "aadhaar_number")


@admin.register(ApplicantDetails)
class ApplicantDetailsAdmin(admin.ModelAdmin):
    list_display = ("user", "company_name", "business_name","employment_type", "current_salary", "cibil_score")
    search_fields = ("user__email", "employment_type")


@admin.register(LenderDetails)
class LenderDetailsAdmin(admin.ModelAdmin):
    list_display = ("user", "lender_type", "bank_firm_name", "gst_number", "dsa_code")
    search_fields = ("user__email", "lender_type", "gst_number")


@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ("loan_id", "applicant", "loan_type", "amount_requested", "status", "created_at")
    list_filter = ("status", "created_at", "loan_type")
    search_fields = ("loan_id", "applicant__username", "applicant__email")


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("txn_id", "user", "loan_request", "amount", "payment_method", "status", "created_at")
    search_fields = ("txn_id", "user__email", "loan_request__loan_id")
    list_filter = ("status", "payment_method", "created_at")
    readonly_fields = ("created_at", "updated_at", "raw_response")

    fieldsets = (
        ("Transaction Details", {
            "fields": ("txn_id", "user", "loan_request", "amount", "payment_method", "status")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
        }),
        ("Raw Response (from PhonePe)", {
            "classes": ("collapse",),
            "fields": ("raw_response",),
        }),
    )



@admin.register(PageAd)
class PageAdAdmin(admin.ModelAdmin):
    list_display = ("title", "page", "position", "size", "is_active", "created_at")
    list_filter = ("page", "position", "size", "is_active")
    search_fields = ("title",)
