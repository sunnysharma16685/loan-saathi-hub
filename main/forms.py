from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Profile, ApplicantDetails, LenderDetails


# -----------------------------
# USER REGISTRATION FORMS
# -----------------------------
class ApplicantRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["email", "password"]

    full_name = forms.CharField(max_length=200)
    pan_number = forms.CharField(max_length=20)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "applicant"
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                full_name=self.cleaned_data["full_name"],
                pan_number=self.cleaned_data["pan_number"],
            )
            ApplicantDetails.objects.create(user=user)
        return user


class LenderRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["email", "password"]

    business_type = forms.CharField(max_length=100, required=False)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "lender"
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            Profile.objects.create(user=user, pan_number="TEMP-PAN")  # PAN optional for lender
            LenderDetails.objects.create(
                user=user,
                business_type=self.cleaned_data.get("business_type", "")
            )
        return user


# -----------------------------
# LOGIN FORM
# -----------------------------
class LoginForm(AuthenticationForm):
    username = forms.EmailField(label="Email")
