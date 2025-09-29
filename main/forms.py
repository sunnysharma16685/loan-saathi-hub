from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import (
    User,
    Profile,
    ApplicantDetails,
    LenderDetails,
    SupportTicket,
    Complaint,
    Feedback,
)
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import re


# -----------------------------
# USER REGISTRATION FORMS
# -----------------------------
class ApplicantRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    # Profile fields
    full_name = forms.CharField(max_length=200, required=False)
    mobile = forms.CharField(max_length=20, required=True)
    gender = forms.CharField(max_length=20, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    pincode = forms.CharField(max_length=10, required=True)
    city = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=100, required=True)

    pancard_number = forms.CharField(max_length=10, required=True)
    aadhaar_number = forms.CharField(max_length=12, required=True)

    dob = forms.DateField(required=False)

    # ApplicantDetails fields
    job_type = forms.CharField(max_length=100, required=False)
    cibil_score = forms.IntegerField(required=False)
    employment_type = forms.CharField(max_length=100, required=False)
    company_name = forms.CharField(max_length=200, required=False)
    company_type = forms.CharField(max_length=200, required=False)
    designation = forms.CharField(max_length=200, required=False)
    itr = forms.CharField(widget=forms.Textarea, required=False)
    current_salary = forms.DecimalField(max_digits=12, decimal_places=2, required=False)
    other_income = forms.DecimalField(max_digits=12, decimal_places=2, required=False)
    total_emi = forms.DecimalField(max_digits=12, decimal_places=2, required=False)

    business_name = forms.CharField(max_length=200, required=False)
    business_type = forms.CharField(max_length=200, required=False)
    business_sector = forms.CharField(max_length=200, required=False)
    total_turnover = forms.DecimalField(max_digits=15, decimal_places=2, required=False)
    last_year_turnover = forms.DecimalField(max_digits=15, decimal_places=2, required=False)
    business_total_emi = forms.DecimalField(max_digits=12, decimal_places=2, required=False)
    business_itr_status = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ["email", "password"]

    # -----------------------------
    # Custom Validation
    # -----------------------------
    def clean_pancard_number(self):
        pancard = self.cleaned_data.get("pancard_number", "").upper()
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pancard):
            raise ValidationError("Invalid PAN format. Example: ABCDE1234F")
        if Profile.objects.filter(pancard_number=pancard).exists():
            raise ValidationError(f"PAN {pancard} already exists.")
        return pancard

    def clean_aadhaar_number(self):
        aadhaar = self.cleaned_data.get("aadhaar_number", "")
        aadhaar = aadhaar.replace(" ", "")  # ✅ remove spaces
        if not re.match(r"^\d{12}$", aadhaar):
            raise ValidationError("Invalid Aadhaar format. Must be exactly 12 digits.")
        if Profile.objects.filter(aadhaar_number=aadhaar).exists():
            raise ValidationError(f"Aadhaar {aadhaar} already exists.")
        return aadhaar

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone and (not phone.isdigit() or len(phone) != 10):
            raise forms.ValidationError("Enter a valid 10-digit phone number")
        return phone
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "applicant"
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()

            # Profile create
            Profile.objects.create(
                user=user,
                full_name=self.cleaned_data.get("full_name"),
                mobile=self.cleaned_data.get("mobile"),
                gender=self.cleaned_data.get("gender"),
                address=self.cleaned_data.get("address"),
                pincode=self.cleaned_data.get("pincode"),
                city=self.cleaned_data.get("city"),
                state=self.cleaned_data.get("state"),
                pancard_number=self.cleaned_data.get("pancard_number"),
                aadhaar_number=self.cleaned_data.get("aadhaar_number"),
                dob=self.cleaned_data.get("dob"),
            )

            # ApplicantDetails create
            ApplicantDetails.objects.create(
                user=user,
                job_type=self.cleaned_data.get("job_type"),
                cibil_score=self.cleaned_data.get("cibil_score"),
                employment_type=self.cleaned_data.get("employment_type"),
                company_name=self.cleaned_data.get("company_name"),
                company_type=self.cleaned_data.get("company_type"),
                designation=self.cleaned_data.get("designation"),
                itr=self.cleaned_data.get("itr"),
                current_salary=self.cleaned_data.get("current_salary"),
                other_income=self.cleaned_data.get("other_income"),
                total_emi=self.cleaned_data.get("total_emi"),
                business_name=self.cleaned_data.get("business_name"),
                business_type=self.cleaned_data.get("business_type"),
                business_sector=self.cleaned_data.get("business_sector"),
                total_turnover=self.cleaned_data.get("total_turnover"),
                last_year_turnover=self.cleaned_data.get("last_year_turnover"),
                business_total_emi=self.cleaned_data.get("business_total_emi"),
                business_itr_status=self.cleaned_data.get("business_itr_status"),
            )
        return user


class LenderRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    # Profile fields
    full_name = forms.CharField(max_length=200, required=False)
    mobile = forms.CharField(max_length=20, required=True)
    gender = forms.CharField(max_length=20, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    pincode = forms.CharField(max_length=10, required=True)
    city = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=100, required=True)

    pancard_number = forms.CharField(max_length=10, required=True)
    aadhaar_number = forms.CharField(max_length=12, required=True)

    # LenderDetails fields
    lender_type = forms.CharField(max_length=100, required=False)
    dsa_code = forms.CharField(max_length=50, required=False)
    bank_firm_name = forms.CharField(max_length=200, required=False)
    gst_number = forms.CharField(max_length=50, required=False)
    branch_name = forms.CharField(max_length=200, required=False)
    designation = forms.CharField(max_length=100, required=False)

    class Meta:
        model = User
        fields = ["email", "password"]

    def clean_pancard_number(self):
        pancard = self.cleaned_data.get("pancard_number", "").upper()
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pancard):
            raise ValidationError("Invalid PAN format. Example: ABCDE1234F")
        if Profile.objects.filter(pancard_number=pancard).exists():
            raise ValidationError(f"PAN {pancard} already exists.")
        return pancard

    def clean_aadhaar_number(self):
        aadhaar = self.cleaned_data.get("aadhaar_number", "")
        aadhaar = aadhaar.replace(" ", "")  # ✅ remove spaces
        if not re.match(r"^\d{12}$", aadhaar):
            raise ValidationError("Invalid Aadhaar format. Must be exactly 12 digits.")
        if Profile.objects.filter(aadhaar_number=aadhaar).exists():
            raise ValidationError(f"Aadhaar {aadhaar} already exists.")
        return aadhaar
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "lender"
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()

            # Profile create
            Profile.objects.create(
                user=user,
                full_name=self.cleaned_data.get("full_name"),
                mobile=self.cleaned_data.get("mobile"),
                gender=self.cleaned_data.get("gender"),
                address=self.cleaned_data.get("address"),
                pincode=self.cleaned_data.get("pincode"),
                city=self.cleaned_data.get("city"),
                state=self.cleaned_data.get("state"),
                pancard_number=self.cleaned_data.get("pancard_number"),
                aadhaar_number=self.cleaned_data.get("aadhaar_number"),
            )

            # LenderDetails create
            LenderDetails.objects.create(
                user=user,
                lender_type=self.cleaned_data.get("lender_type"),
                dsa_code=self.cleaned_data.get("dsa_code"),
                bank_firm_name=self.cleaned_data.get("bank_firm_name"),
                gst_number=self.cleaned_data.get("gst_number"),
                branch_name=self.cleaned_data.get("branch_name"),
                designation=self.cleaned_data.get("designation"),
            )
        return user

# -----------------------------
# PROFILE UPDATE FORM
# -----------------------------
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "full_name",
            "mobile",
            "gender",
            "address",
            "pincode",
            "city",
            "state",
            "pancard_number",
            "aadhaar_number",
            "dob",
        ]

    # PAN Validation
    def clean_pancard_number(self):
        pancard = self.cleaned_data.get("pancard_number", "").upper()
        if pancard and not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pancard):
            raise ValidationError("Invalid PAN format. Example: ABCDE1234F")
        return pancard

    # Aadhaar Validation
    def clean_aadhaar_number(self):
        aadhaar = self.cleaned_data.get("aadhaar_number", "")
        aadhaar = aadhaar.replace(" ", "")  # ✅ remove spaces
        if aadhaar and not re.match(r"^\d{12}$", aadhaar):
            raise ValidationError("Invalid Aadhaar format. Must be exactly 12 digits.")
        return aadhaar

    # Phone Validation
    def clean_mobile(self):
        mobile = self.cleaned_data.get("mobile")
        if mobile and (not mobile.isdigit() or len(mobile) != 10):
            raise ValidationError("Enter a valid 10-digit phone number")
        return mobile

# -----------------------------
# LOGIN FORM
# -----------------------------
class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")


# -----------------------------
# FOOTER FORMS
# -----------------------------
class SupportForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name (optional)", "class": "form-control"}),
            "email": forms.EmailInput(attrs={"placeholder": "Your email", "class": "form-control"}),
            "subject": forms.TextInput(attrs={"placeholder": "Subject", "class": "form-control"}),
            "message": forms.Textarea(attrs={"rows": 4, "maxlength": 2000, "class": "form-control"}),
        }


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ["name", "email", "complaint_against", "against_role", "message"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Your name (optional)", "class": "form-control"}),
            "email": forms.EmailInput(attrs={"placeholder": "Your email", "class": "form-control"}),
            "complaint_against": forms.TextInput(attrs={"placeholder": "Email or User ID (if known)", "class": "form-control"}),
            "against_role": forms.Select(attrs={"class": "form-select"}),
            "message": forms.Textarea(attrs={"rows": 5, "maxlength": 2000, "placeholder": "Describe complaint (max ~250 words)", "class": "form-control"}),
        }

    def clean_message(self):
        data = self.cleaned_data.get("message", "")
        if len(data.split()) > 250:
            raise forms.ValidationError("Please limit to about 250 words.")
        return data


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["role", "name", "email", "rating", "message"]
        widgets = {
            "role": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"placeholder": "Name (if logged in will prefill)", "class": "form-control"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email (if logged in will prefill)", "class": "form-control"}),
            "rating": forms.Select(
                choices=[("", "Choose..."), (1, "★☆☆☆☆"), (2, "★★☆☆☆"), (3, "★★★☆☆"), (4, "★★★★☆"), (5, "★★★★★")],
                attrs={"class": "form-select"},
            ),
            "message": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }

