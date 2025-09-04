from django.contrib import admin
from .models import (
    User,
    Profile,
    ApplicantDetails,
    LenderDetails,
    LoanRequest,
    LoanLenderStatus,
    Payment
)

# -------------------- User --------------------
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email',)
    ordering = ('email',)


# -------------------- Profile --------------------
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'mobile', 'city', 'state')
    search_fields = ('full_name', 'user__email', 'mobile', 'city', 'state')
    list_filter = ('state', 'city', 'marital_status')


# -------------------- Applicant Details --------------------
@admin.register(ApplicantDetails)
class ApplicantDetailsAdmin(admin.ModelAdmin):
    list_display = ('user', 'employment_type', 'company_name', 'business_name', 'cibil_score')
    search_fields = ('user__email', 'company_name', 'business_name')
    list_filter = ('employment_type',)


# -------------------- Lender Details --------------------
@admin.register(LenderDetails)
class LenderDetailsAdmin(admin.ModelAdmin):
    list_display = ('user', 'lender_type', 'bank_firm_name', 'branch_name', 'dsa_code')
    search_fields = ('user__email', 'bank_firm_name', 'branch_name', 'dsa_code')
    list_filter = ('lender_type',)


# -------------------- Loan Request --------------------
@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ('loan_id', 'applicant', 'loan_type', 'amount_requested', 'duration_months', 'status', 'created_at')
    search_fields = ('loan_id', 'applicant__email', 'loan_type')
    list_filter = ('loan_type', 'status', 'created_at')


# -------------------- Loan Lender Status --------------------
@admin.register(LoanLenderStatus)
class LoanLenderStatusAdmin(admin.ModelAdmin):
    list_display = ('loan', 'lender', 'status')
    search_fields = ('loan__loan_id', 'lender__email')
    list_filter = ('status',)


# -------------------- Payment --------------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('loan_request', 'lender', 'amount', 'payment_method', 'status', 'created_at')
    search_fields = ('loan_request__loan_id', 'lender__email')
    list_filter = ('status', 'payment_method', 'created_at')
