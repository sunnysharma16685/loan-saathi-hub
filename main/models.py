from django.db import models
from django.contrib.auth.models import AbstractUser


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
