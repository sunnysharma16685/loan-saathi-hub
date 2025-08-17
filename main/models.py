from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.utils.crypto import get_random_string


# ==============================
# Custom User Manager
# ==============================
class UserManager(BaseUserManager):
    def create_user(self, email=None, mobile=None, password=None, role="user", **extra_fields):
        if not email and not mobile:
            raise ValueError("User must have either an email or a mobile number.")

        if email:
            email = self.normalize_email(email)

        user = self.model(email=email, mobile=mobile, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, mobile=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email=email, mobile=mobile, password=password, role="admin", **extra_fields)


# ==============================
# Custom User Model (No Username)
# ==============================
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('agent', 'Agent'),
        ('admin', 'Admin'),
    )

    email = models.EmailField(unique=True, null=True, blank=True)
    mobile = models.CharField(max_length=15, unique=True, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")

    first_name = models.CharField(max_length=50, blank=True, null=True)
    last_name = models.CharField(max_length=50, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "mobile"   # ✅ primary login with mobile
    REQUIRED_FIELDS = ["email"]  # ✅ email required on createsuperuser

    def __str__(self):
        return self.email or self.mobile or f"User {self.id}"


# ==============================
# User Profile
# ==============================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Step 1: Basic
    title = models.CharField(max_length=10, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)

    # Step 2: Job
    occupation = models.CharField(max_length=100, blank=True, null=True)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    turnover = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"UserProfile - {self.user.mobile or self.user.email}"


# ==============================
# Agent Profile
# ==============================
class AgentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # Step 1: Personal
    title = models.CharField(max_length=10, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pan_number = models.CharField(max_length=10, blank=True, null=True)

    # Step 2: Business
    business_type = models.CharField(max_length=50, blank=True, null=True)
    gst_no = models.CharField(max_length=20, blank=True, null=True)
    dsa_code = models.CharField(max_length=50, blank=True, null=True)
    business_name = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    turnover = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"AgentProfile - {self.user.mobile or self.user.email}"


# ==============================
# Loan Request
# ==============================
class LoanRequest(models.Model):
    loan_id = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    loan_type = models.CharField(max_length=100)
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2)
    duration_months = models.IntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    remarks = models.TextField(blank=True, null=True)

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.loan_id:
            self.loan_id = "LSH" + get_random_string(6, allowed_chars="0123456789")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Loan {self.loan_id} - {self.user.mobile or self.user.email}"


# ==============================
# Payment
# ==============================
class Payment(models.Model):
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    loan_request = models.ForeignKey(LoanRequest, on_delete=models.CASCADE, related_name="payments")

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50)

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.id} - Loan {self.loan_request.loan_id}"
