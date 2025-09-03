from django.contrib import admin
from .models import (
    User,
    Profile,
    ApplicantDetails,
    LenderDetails,
    LoanRequest,
    Payment,
)


# ------------------ Custom Admin Classes ------------------

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("user_id", "email", "role", "created_at")
    list_filter = ("role",)
    search_fields = ("email", "user_id")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "mobile", "pan_number", "city", "state")
    search_fields = ("full_name", "mobile", "pan_number")


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


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("loan_request", "lender", "amount", "status", "created_at")
    search_fields = ("loan_request__loan_id", "lender__email")
    list_filter = ("status", "payment_method")
