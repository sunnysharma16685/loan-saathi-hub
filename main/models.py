from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
import uuid
from django.utils.timezone import now


# ---------------------------
# USER MANAGER
# ---------------------------
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with email + password."""
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser (Django admin)."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")   # ensure admin role
        return self.create_user(email, password, **extra_fields)


# ---------------------------
# CUSTOM USER MODEL
# ---------------------------
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("applicant", "Applicant"),
        ("lender", "Lender"),
        ("admin", "Admin"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=20, unique=True, editable=False)  # LSHA0001 / LSHL0001 / LSHAD0001
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(default=now)

    # Django required fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def save(self, *args, **kwargs):
        """Auto-generate user_id based on role."""
        if not self.user_id:
            if self.role == "applicant":
                prefix = "LSHA"
            elif self.role == "lender":
                prefix = "LSHL"
            else:  # admin
                prefix = "LSHAD"

            last_user = User.objects.filter(role=self.role).order_by("-created_at").first()
            if last_user and last_user.user_id:
                try:
                    last_number = int(last_user.user_id[-4:])
                except ValueError:
                    last_number = 0
                new_number = str(last_number + 1).zfill(4)
            else:
                new_number = "0001"

            self.user_id = f"{prefix}{new_number}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user_id} - {self.email} ({self.role})"


# ---------------------------
# COMMON PROFILE TABLE
# ---------------------------
class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    full_name = models.CharField(max_length=200, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    marital_status = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)

    pan_number = models.CharField(max_length=20)  # Mandatory
    aadhaar = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.user_id} - {self.full_name}"


# ---------------------------
# APPLICANT DETAILS
# ---------------------------
class ApplicantDetails(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="applicant_details")

    loan_purpose = models.TextField(blank=True, null=True)
    employment_type = models.CharField(max_length=100, blank=True, null=True)
    job_type = models.CharField(max_length=100, blank=True, null=True)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    other_income = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    cibil_score = models.IntegerField(blank=True, null=True)
    itr = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Applicant Details for {self.user.user_id}"


# ---------------------------
# LENDER DETAILS
# ---------------------------
class LenderDetails(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="lender_details")

    business_type = models.CharField(max_length=100, blank=True, null=True)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    turnover = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    dsa_code = models.CharField(max_length=50, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Lender Details for {self.user.user_id}"



# -------------------------------
# LOAN REQUESTS
# -------------------------------
class LoanRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan_id = models.CharField(max_length=20, unique=True)
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loan_requests")

    loan_type = models.CharField(max_length=100)
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2)
    duration_months = models.IntegerField()

    # Textbox me applicant 1% - 100% tak daale
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Enter interest rate between 1% and 100%"
    )

    reason_for_loan = models.CharField(max_length=200, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)

    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(default=now)

    def clean(self):
        if self.applicant.role != "applicant":
            raise ValidationError("Only Applicant users can create Loan Requests.")

        if self.interest_rate < 1 or self.interest_rate > 100:
            raise ValidationError("Interest rate must be between 1% and 100%.")

    def __str__(self):
        return f"{self.loan_id} - {self.applicant.email}"



# -------------------------------
# PAYMENTS
# -------------------------------
class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    loan_request = models.ForeignKey(LoanRequest, on_delete=models.CASCADE, related_name="payments")
    payment_method = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(default=now)

    def clean(self):
        if self.lender.role != "lender":
            raise ValidationError("Only Lender users can make Payments.")

    def __str__(self):
        return f"Payment {self.id} - {self.amount} ({self.status})"
