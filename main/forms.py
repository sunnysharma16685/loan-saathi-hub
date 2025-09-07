from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Profile, applicantdetails, lenderdetails


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
    pancard_number = forms.CharField(max_length=20, required=False)
    aadhaar_number = forms.CharField(max_length=20, required=False)
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
            applicantdetails.objects.create(
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

    # Profile fields (basic)
    full_name = forms.CharField(max_length=200, required=False)
    mobile = forms.CharField(max_length=20, required=True)
    gender = forms.CharField(max_length=20, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    pincode = forms.CharField(max_length=10, required=True)
    city = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=100, required=True)
    pancard_number = forms.CharField(max_length=20, required=False)
    aadhaar_number = forms.CharField(max_length=20, required=False)

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
            lenderdetails.objects.create(
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
# LOGIN FORM
# -----------------------------
class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")
