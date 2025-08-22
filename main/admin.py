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
    list_display = ("user", "loan_purpose", "employment_type", "monthly_income", "cibil_score")
    search_fields = ("user__email", "loan_purpose")


@admin.register(LenderDetails)
class LenderDetailsAdmin(admin.ModelAdmin):
    list_display = ("user", "business_type", "gst_number", "turnover", "dsa_code")
    search_fields = ("user__email", "business_type", "gst_number")


@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ("loan_id", "applicant", "loan_type", "amount_requested", "status", "created_at")
    search_fields = ("loan_id", "applicant__email")
    list_filter = ("status", "loan_type")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("loan_request", "lender", "amount", "status", "created_at")
    search_fields = ("loan_request__loan_id", "lender__email")
    list_filter = ("status", "payment_method")
