import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver

# =====================================================
# USER MANAGER
# =====================================================
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email: raise ValueError("Users must have an email address")
        email = self.normalize_email(email); user = self.model(email=email, **extra_fields)
        user.set_password(password); user.save(using=self._db); return user
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True); extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin"); return self.create_user(email, password, **extra_fields)

# =====================================================
# CUSTOM USER MODEL
# =====================================================
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [("applicant","Applicant"),("lender","Lender"),("admin","Admin")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True); is_staff = models.BooleanField(default=False)
    USERNAME_FIELD = "email"; REQUIRED_FIELDS: list[str] = []
    objects = UserManager()
    def save(self,*a,**kw):
        if not self.user_id:
            prefix = "LSHA" if self.role=="applicant" else "LSHL" if self.role=="lender" else "LSHAD"
            last = User.objects.filter(role=self.role).order_by("-created_at").first()
            last_num = int(last.user_id[-4:]) if last and last.user_id and last.user_id[-4:].isdigit() else 0
            self.user_id = f"{prefix}{str(last_num+1).zfill(4)}"
        super().save(*a,**kw)
    def __str__(self): return f"{self.user_id} - {self.email} ({self.role})"

# =====================================================
# PROFILE
# =====================================================
class Profile(models.Model):
    STATUS_CHOICES = [("Hold","Hold"),("Active","Active"),("Deactivated","Deactivated"),("Deleted","Deleted")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="profile")
    full_name = models.CharField(max_length=255); mobile=models.CharField(max_length=20,blank=True,null=True)
    dob=models.DateField(blank=True,null=True); gender=models.CharField(max_length=20,blank=True,null=True)
    marital_status=models.CharField(max_length=50,blank=True,null=True)
    address=models.TextField(blank=True,null=True)
    pancard_number=models.CharField(max_length=10,unique=True,help_text="ABCDE1234F")
    aadhaar_number=models.CharField(max_length=12,unique=True,help_text="12-digit Aadhaar")
    pincode=models.CharField(max_length=10,blank=True,null=True); city=models.CharField(max_length=50,blank=True,null=True)
    state=models.CharField(max_length=50,blank=True,null=True)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES,default="Hold")
    is_reviewed=models.BooleanField(default=False); is_blocked=models.BooleanField(default=False)
    delete_reason=models.TextField(blank=True,null=True)  # ✅ added field
    def __str__(self): return f"{self.full_name} ({self.status})"

# =====================================================
# APPLICANT DETAILS
# =====================================================
class ApplicantDetails(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name="applicant_details")
    job_type=models.CharField(max_length=50,blank=True,null=True); cibil_score=models.IntegerField(blank=True,null=True)
    cibil_last_generated=models.DateTimeField(blank=True,null=True)
    cibil_generated_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True,related_name="generated_cibil_scores")
    employment_type=models.CharField(max_length=50,blank=True,null=True); company_name=models.CharField(max_length=255,blank=True,null=True)
    company_type=models.CharField(max_length=255,blank=True,null=True); designation=models.CharField(max_length=255,blank=True,null=True)
    itr=models.TextField(blank=True,null=True); current_salary=models.DecimalField(max_digits=12,decimal_places=2,blank=True,null=True)
    other_income=models.DecimalField(max_digits=12,decimal_places=2,blank=True,null=True); total_emi=models.DecimalField(max_digits=12,decimal_places=2,blank=True,null=True)
    business_name=models.CharField(max_length=255,blank=True,null=True); business_type=models.CharField(max_length=255,blank=True,null=True)
    business_sector=models.CharField(max_length=255,blank=True,null=True); total_turnover=models.DecimalField(max_digits=15,decimal_places=2,blank=True,null=True)
    last_year_turnover=models.DecimalField(max_digits=15,decimal_places=2,blank=True,null=True); business_total_emi=models.DecimalField(max_digits=12,decimal_places=2,blank=True,null=True)
    business_itr_status=models.CharField(max_length=255,blank=True,null=True)
    created_at=models.DateTimeField(default=timezone.now); updated_at=models.DateTimeField(auto_now=True)
    def __str__(self): return f"Applicant {self.user.user_id}"

# =====================================================
# LENDER DETAILS
# =====================================================
class LenderDetails(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name="lender_details")
    lender_type=models.CharField(max_length=255,blank=True,null=True); dsa_code=models.CharField(max_length=50,blank=True,null=True)
    bank_firm_name=models.CharField(max_length=255,blank=True,null=True); gst_number=models.CharField(max_length=50,blank=True,null=True)
    branch_name=models.CharField(max_length=255,blank=True,null=True); designation=models.CharField(max_length=100,blank=True,null=True)
    created_at=models.DateTimeField(default=timezone.now); updated_at=models.DateTimeField(auto_now=True)
    def __str__(self): return f"Lender {self.user.user_id}"

# =====================================================
# LOAN REQUEST
# =====================================================
class LoanRequest(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    loan_id=models.CharField(max_length=100,unique=True)
    applicant=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="loan_requests")
    loan_type=models.CharField(max_length=100,blank=True,null=True); amount_requested=models.DecimalField(max_digits=12,decimal_places=2)
    duration_months=models.IntegerField(); interest_rate=models.DecimalField(max_digits=5,decimal_places=2)
    reason_for_loan=models.TextField(blank=True,null=True)
    status=models.CharField(max_length=20,choices=[("Pending","Pending"),("Approved","Approved"),("Rejected","Rejected"),("Hold","Hold"),("Accepted","Accepted")],default="Pending")
    accepted_lender=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="accepted_loans")
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.loan_id

# =====================================================
# LOAN LENDER STATUS
# =====================================================
class LoanLenderStatus(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    loan=models.ForeignKey(LoanRequest,on_delete=models.CASCADE,related_name="lender_statuses")
    lender=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="lender_decisions")
    status=models.CharField(max_length=50,choices=[("Pending","Pending"),("Approved","Approved"),("Rejected","Rejected")],default="Pending")
    remarks=models.TextField(blank=True,null=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: unique_together=("loan","lender")
    def __str__(self): return f"{self.lender}-{self.loan.loan_id}({self.status})"

# =====================================================
# PAYMENT TRANSACTIONS (Razorpay Integrated)
# =====================================================
class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    loan_request = models.ForeignKey(
        "main.LoanRequest",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    txn_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=50, default="Razorpay")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    raw_response = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.txn_id} ({self.status})"

    class Meta:
        ordering = ["-created_at"]



# =====================================================
# SUPPORT / COMPLAINT / FEEDBACK / CIBIL
# =====================================================
class SupportTicket(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name=models.CharField(max_length=150,blank=True,null=True); email=models.EmailField()
    subject=models.CharField(max_length=255); message=models.TextField()
    created_at=models.DateTimeField(default=timezone.now); resolved=models.BooleanField(default=False)
    def __str__(self): return f"Support({self.email}-{self.subject})"

class Complaint(models.Model):
    ROLE_CHOICES=(("applicant","Applicant"),("lender","Lender"),("guest","Guest"))
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name=models.CharField(max_length=150,blank=True); email=models.EmailField()
    complaint_against=models.CharField(max_length=255,blank=True); against_role=models.CharField(max_length=20,choices=ROLE_CHOICES,default="guest")
    message=models.TextField(); created_at=models.DateTimeField(default=timezone.now); handled=models.BooleanField(default=False)
    def __str__(self): return f"Complaint({self.email}->{self.complaint_against})"

class Feedback(models.Model):
    ROLE_CHOICES=(("applicant","Applicant"),("lender","Lender"),("guest","Guest"))
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    role=models.CharField(max_length=20,choices=ROLE_CHOICES,default="guest"); name=models.CharField(max_length=150,blank=True)
    email=models.EmailField(blank=True,null=True); user=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL)
    rating=models.PositiveSmallIntegerField(null=True,blank=True); message=models.TextField(blank=True)
    created_at=models.DateTimeField(default=timezone.now)
    def __str__(self): return f"Feedback({self.role}-{self.email or ''}-{self.rating})"

class CibilReport(models.Model):
    loan=models.ForeignKey(LoanRequest,on_delete=models.CASCADE,related_name="cibil_reports")
    lender=models.ForeignKey(User,on_delete=models.CASCADE,related_name="cibil_reports")
    score=models.PositiveSmallIntegerField(null=True,blank=True); raw_response=models.JSONField(null=True,blank=True)
    created_at=models.DateTimeField(default=timezone.now)
    class Meta: ordering=["-created_at"]; verbose_name="CIBIL Report"; verbose_name_plural="CIBIL Reports"
    def __str__(self): return f"CIBIL-{self.loan.loan_id} by {self.lender.email}"

# =====================================================
# SIGNALS
# =====================================================
@receiver(post_save,sender=User)
def create_user_profile(sender,instance,created,**kw): 
    if created: pass

# =====================================================
# DELETED USER LOG
# =====================================================
class DeletedUserLog(models.Model):
    email=models.EmailField(); mobile=models.CharField(max_length=15,null=True,blank=True)
    pancard_number=models.CharField(max_length=20,null=True,blank=True); aadhaar_number=models.CharField(max_length=20,null=True,blank=True)
    reason=models.TextField(); deleted_at=models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.email}-{self.reason[:30]}"


# =====================================================
# ADVERTISEMENT
# =====================================================
class PageAd(models.Model):
    PAGE_CHOICES = [
        ("loan_request", "Loan Request Page"),
        ("dashboard_admin", "Admin Dashboard"),
        ("dashboard_applicant", "Applicant Dashboard"),
        ("dashboard_lender", "Lender Dashboard"),
        ("profile_form", "Profile Form"),
        ("edit_profile", "Edit Profile"),
        ("review_profile", "Review Profile"),
        ("edit_profile", "Edit Profile"),
        ("partial_profile", "Partial Profile"),
        ("view_profile", "View Profile"),
        ("register", "Register Page"),
        ("login", "Login Page"),
    ]
    SIZE_CHOICES = [
        ("small", "Small (200x200)"),
        ("medium", "Medium (400x250)"),
        ("big", "Big (728x90 Banner)"),
    ]
    POSITION_CHOICES = [
        ("left", "Left"),
        ("right", "Right"),
        ("top", "Top"),
        ("bottom", "Bottom"),
        ("inline", "Inside Content"),
    ]

    page = models.CharField(max_length=50, choices=PAGE_CHOICES)
    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to="ads/")
    link = models.URLField(blank=True, null=True)
    size = models.CharField(max_length=20, choices=SIZE_CHOICES, default="medium")
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, default="right")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.page} - {self.position})"

