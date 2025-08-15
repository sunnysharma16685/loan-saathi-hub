# loan_saathi_hub.py
# ==============================
# Combined Django code for Loan Saathi Hub
# ==============================

# ------------------------
# Imports
# ------------------------
from django.contrib import admin
from django.urls import path
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.shortcuts import render, redirect
from django.http import HttpResponse

# ------------------------
# Models
# ------------------------

# Custom User Model
class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'Loan User'),
        ('agent', 'Loan Agent'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    mobile = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


# User Profile
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    dob = models.DateField()
    gender = models.CharField(max_length=10)
    marital_status = models.CharField(max_length=20)
    nationality = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='photos/', null=True, blank=True)
    pan_number = models.CharField(max_length=20)
    voter_id = models.CharField(max_length=20)
    passport_no = models.CharField(max_length=20, blank=True, null=True)
    driving_license = models.CharField(max_length=20, blank=True, null=True)
    bank_account_no = models.CharField(max_length=30)
    ifsc_code = models.CharField(max_length=20)
    reason_for_loan = models.TextField()
    occupation = models.CharField(max_length=100)
    company_name = models.CharField(max_length=200, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    turnover = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


# Agent Profile
class AgentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    dob = models.DateField()
    gender = models.CharField(max_length=10)
    marital_status = models.CharField(max_length=20)
    nationality = models.CharField(max_length=50)
    photo = models.ImageField(upload_to='photos/', null=True, blank=True)
    pan_number = models.CharField(max_length=20)
    voter_id = models.CharField(max_length=20)
    passport_no = models.CharField(max_length=20, blank=True, null=True)
    driving_license = models.CharField(max_length=20, blank=True, null=True)
    bank_account_no = models.CharField(max_length=30)
    ifsc_code = models.CharField(max_length=20)
    business_type = models.CharField(max_length=50)
    gst_no = models.CharField(max_length=20, blank=True, null=True)
    dsa_code_name = models.CharField(max_length=200, blank=True, null=True)
    business_name = models.CharField(max_length=200)
    designation = models.CharField(max_length=100)
    turnover = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Agent Profile of {self.user.username}"


# Loan Request
class LoanRequest(models.Model):
    LOAN_TYPES = (
        ('personal', 'Personal Loan'),
        ('home', 'Home Loan'),
        ('business', 'Business Loan'),
        ('vehicle', 'Vehicle Loan'),
        ('agriculture', 'Agriculture Loan'),
        ('mudra', 'Mudra Loan'),
        ('overdraft', 'Overdraft Loan'),
    )
    loan_id = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'user'})
    loan_type = models.CharField(max_length=20, choices=LOAN_TYPES)
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2)
    duration_months = models.IntegerField()
    interest_rate = models.CharField(max_length=20)  # store range like "7%-15%"
    status = models.CharField(max_length=20, default='pending')
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.loan_id} - {self.user.username}"


# Payment
class Payment(models.Model):
    agent = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'agent'})
    loan_request = models.ForeignKey(LoanRequest, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=50)  # UPI, Credit Card, etc.
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')  # pending, done
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Payment for {self.loan_request.loan_id} by {self.agent.username}"


# ------------------------
# Admin Registration
# ------------------------
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'mobile', 'email', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'mobile', 'email')
    list_editable = ('is_active',)
    ordering = ('-date_joined',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'dob', 'gender', 'occupation', 'company_name')
    search_fields = ('full_name', 'user__username', 'pan_number')
    list_filter = ('gender', 'occupation')


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'dob', 'gender', 'business_type', 'business_name')
    search_fields = ('full_name', 'user__username', 'pan_number', 'gst_no')
    list_filter = ('gender', 'business_type')


@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ('loan_id', 'user', 'loan_type', 'amount_requested', 'duration_months', 'interest_rate', 'status')
    list_filter = ('loan_type', 'status')
    search_fields = ('loan_id', 'user__username')
    ordering = ('-loan_id',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('agent', 'loan_request', 'payment_method', 'amount', 'status', 'transaction_id')
    list_filter = ('payment_method', 'status')
    search_fields = ('agent__username', 'loan_request__loan_id', 'transaction_id')


# ------------------------
# Views
# ------------------------
def index(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type')
        email_or_mobile = request.POST.get('email_or_mobile')
        password = request.POST.get('password')

        if not email_or_mobile or not password:
            return render(request, 'login.html', {'error': 'All fields are required!'})

        if user_type == 'user':
            return redirect('dashboard_user')
        else:
            return redirect('dashboard_agent')
    return render(request, 'login.html')

def complete_profile_user(request):
    if request.method == 'POST':
        return redirect('dashboard_user')
    return render(request, 'complete_profile_user.html')

def complete_profile_agent(request):
    if request.method == 'POST':
        return redirect('dashboard_agent')
    return render(request, 'complete_profile_agent.html')

def dashboard_user(request):
    return render(request, 'dashboard_user.html')

def dashboard_agent(request):
    return render(request, 'dashboard_agent.html')

def loan_request(request):
    if request.method == 'POST':
        return redirect('dashboard_user')
    return render(request, 'loan_request.html')

def payment(request):
    if request.method == 'POST':
        return redirect('dashboard_agent')
    return render(request, 'payment.html')

def about(request):
    return render(request, 'about.html')

def terms(request):
    return render(request, 'terms.html')

def privacy(request):
    return render(request, 'privacy.html')

def faq(request):
    return render(request, 'faq.html')

def support(request):
    return render(request, 'support.html')

def contacts(request):
    return render(request, 'contacts.html')

def feedback(request):
    return render(request, 'feedback.html')


# ------------------------
# URL Patterns
# ------------------------
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('login/', login_view, name='login'),
    path('complete_profile_user/', complete_profile_user, name='complete_profile_user'),
    path('complete_profile_agent/', complete_profile_agent, name='complete_profile_agent'),
    path('dashboard_user/', dashboard_user, name='dashboard_user'),
    path('dashboard_agent/', dashboard_agent, name='dashboard_agent'),
    path('loan_request/', loan_request, name='loan_request'),
    path('payment/', payment, name='payment'),
    path('about/', about, name='about'),
    path('terms/', terms, name='terms'),
    path('privacy/', privacy, name='privacy'),
    path('faq/', faq, name='faq'),
    path('support/', support, name='support'),
    path('contacts/', contacts, name='contacts'),
    path('feedback/', feedback, name='feedback'),
]

# Settings note:
# Add in settings.py → AUTH_USER_MODEL = 'main.User'
