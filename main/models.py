import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# -------------------- User --------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ("applicant", "Applicant"),
        ("lender", "Lender"),
    )
    username = None  # we will use email as login
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.role})"


# -------------------- Profile --------------------
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    marital_status = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    pancard_number = models.CharField(max_length=20, unique=True)
    aadhaar_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.email})"


# -------------------- Applicant Details --------------------
class ApplicantDetails(models.Model):
    EMPLOYMENT_CHOICES = (
        ("Salaried", "Salaried"),
        ("Business", "Business"),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_CHOICES)
    
    # Business fields
    business_name = models.CharField(max_length=255, blank=True, null=True)
    business_type = models.CharField(max_length=100, blank=True, null=True)
    business_sector = models.CharField(max_length=100, blank=True, null=True)
    total_turnover = models.FloatField(blank=True, null=True)
    last_year_turnover = models.FloatField(blank=True, null=True)
    business_total_emi = models.FloatField(blank=True, null=True)
    business_itr_status = models.CharField(max_length=50, blank=True, null=True)

    # Salaried fields
    company_name = models.CharField(max_length=255, blank=True, null=True)
    company_type = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    current_salary = models.FloatField(blank=True, null=True)
    other_income = models.FloatField(blank=True, null=True)
    total_emi = models.FloatField(blank=True, null=True)
    itr = models.CharField(max_length=100, blank=True, null=True)

    cibil_score = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"ApplicantDetails: {self.user.email}"


# -------------------- Lender Details --------------------
class LenderDetails(models.Model):
    LENDER_TYPE_CHOICES = (
        ("Bank", "Bank"),
        ("DSA", "DSA"),
        ("Individual", "Individual"),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    lender_type = models.CharField(max_length=20, choices=LENDER_TYPE_CHOICES)
    bank_firm_name = models.CharField(max_length=255, blank=True, null=True)
    branch_name = models.CharField(max_length=100, blank=True, null=True)
    dsa_code = models.CharField(max_length=50, blank=True, null=True)
    designation = models.CharField(max_length=50, blank=True, null=True)
    gst_number = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Lender: {self.user.email}"


# -------------------- Loan Request --------------------
class LoanRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan_id = models.CharField(max_length=20, unique=True)
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loans")
    loan_type = models.CharField(max_length=50)
    amount_requested = models.FloatField()
    duration_months = models.IntegerField()
    interest_rate = models.FloatField()
    reason_for_loan = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default="Pending")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"LoanRequest: {self.loan_id} ({self.status})"


# -------------------- Loan Lender Status --------------------
class LoanLenderStatus(models.Model):
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan = models.ForeignKey(LoanRequest, on_delete=models.CASCADE, related_name="lender_statuses")
    lender = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("loan", "lender")

    def __str__(self):
        return f"{self.loan.loan_id} -> {self.lender.email}: {self.status}"


# -------------------- Payment --------------------
class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ("UPI", "UPI"),
        ("Bank Transfer", "Bank Transfer"),
        ("Credit Card", "Credit Card"),
        ("Dummy", "Dummy"),
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    loan_request = models.ForeignKey(LoanRequest, on_delete=models.CASCADE, related_name="payments")
    lender = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField()
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, default="Pending")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("loan_request", "lender")

    def __str__(self):
        return f"Payment {self.id} - Loan {self.loan_request.loan_id} ({self.status})"
