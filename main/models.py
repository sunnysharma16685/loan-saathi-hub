from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid

# ---------------------------
# USER MANAGER
# ---------------------------
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
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

    # Supabase UID
    supabase_uid = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def save(self, *args, **kwargs):
        if not self.user_id:
            if self.role == "applicant":
                prefix = "LSHA"
            elif self.role == "lender":
                prefix = "LSHL"
            else:
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
# PROFILE - Basic Profile
# ---------------------------
class Profile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    full_name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    marital_status = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # KYC
    pancard_number = models.CharField(max_length=20, unique=True)
    aadhaar_number = models.CharField(max_length=20, blank=True, null=True)

    # Location
    pincode = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.full_name


# ---------------------------
# APPLICANT DETAILS
# ---------------------------
class ApplicantDetails(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="applicant_details")

    job_type = models.CharField(max_length=50, blank=True, null=True)
    cibil_score = models.IntegerField(blank=True, null=True)
    employment_type = models.CharField(max_length=50, blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_type = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=255, blank=True, null=True)
    itr = models.TextField(blank=True, null=True)
    current_salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    other_income = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_emi = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)

    business_name = models.CharField(max_length=255, blank=True, null=True)
    business_type = models.CharField(max_length=255, blank=True, null=True)
    business_sector = models.CharField(max_length=255, blank=True, null=True)
    total_turnover = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    last_year_turnover = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    business_total_emi = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    business_itr_status = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Applicant Details for {self.user.user_id}"


# ---------------------------
# LENDER DETAILS
# ---------------------------
class LenderDetails(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="lender_details")

    lender_type = models.CharField(max_length=255, blank=True, null=True)
    dsa_code = models.CharField(max_length=50, blank=True, null=True)
    bank_firm_name = models.CharField(max_length=255, blank=True, null=True)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Lender Details for {self.user.user_id}"



# -------------------------------
# LOAN REQUEST
# -------------------------------
class LoanRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan_id = models.CharField(max_length=100, unique=True)
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="loan_requests"
    )
    loan_type = models.CharField(max_length=100, blank=True, null=True)
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2)
    duration_months = models.IntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    reason_for_loan = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Approved", "Approved"), ("Rejected", "Rejected")],
        default="Pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.loan_id


# -------------------------------
# LENDER STATUS - Each Lender's decision
# -------------------------------
class LoanLenderStatus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    loan = models.ForeignKey(
        LoanRequest, on_delete=models.CASCADE, related_name="lender_statuses"
    )
    lender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lender_decisions"
    )

    status = models.CharField(
        max_length=50,
        choices=[
            ("Pending", "Pending"),
            ("Approved", "Approved"),
            ("Rejected", "Rejected"),
        ],
        default="Pending",
    )
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("loan", "lender")

    def __str__(self):
        return f"{self.lender} - {self.loan.loan_id} ({self.status})"
# -------------------------------
# PAYMENT
# -------------------------------
class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan_request = models.ForeignKey(LoanRequest, on_delete=models.CASCADE, related_name="payments")
    lender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lender_payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, default="Pending")
    payment_method = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.loan_request.loan_id} - {self.amount} ({self.status})"
