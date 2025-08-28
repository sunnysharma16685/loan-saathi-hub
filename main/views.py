from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm
import uuid

from .models import User, Profile, ApplicantDetails, LenderDetails, LoanRequest, Payment
from main.supabase_client import (
    create_user_in_supabase,
    upsert_profile_in_supabase,
    sync_loan_request_to_supabase,
    sync_payment_to_supabase,
)

# -------------------- Home --------------------
def home(request):
    return render(request, "index.html")


# -------------------- Helper: Profile Check --------------------
def is_profile_complete(user):
    if not Profile.objects.filter(user=user).exists():
        return False
    if user.role == "applicant":
        return ApplicantDetails.objects.filter(user=user).exists()
    if user.role == "lender":
        return LenderDetails.objects.filter(user=user).exists()
    return True


# -------------------- Register --------------------
def register_view(request):
    role = (request.GET.get("role") or "").lower()
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        confirm_password = request.POST.get("confirm_password") or ""
        form_role = (request.POST.get("role") or role).lower()

        # Role validation
        if form_role not in ("applicant", "lender"):
            messages.error(request, "Please select Applicant or Lender.")
            return redirect(f"/register/?role={role or ''}")

        # Email + password check
        if not email or not password:
            messages.error(request, "Email and password are required.")
            return redirect(f"/register/?role={form_role}")

        # Password confirmation check
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect(f"/register/?role={form_role}")

        # Duplicate email check
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect(f"/register/?role={form_role}")

        try:
            # --- Step 1: Local User Create ---
            prefix = "LSHA" if form_role == "applicant" else "LSHL"
            display_user_id = f"{prefix}{get_random_string(4, allowed_chars='0123456789')}"
            local_uuid = uuid.uuid4()
            user = User(
                id=local_uuid,
                email=email,
                role=form_role,
                user_id=display_user_id,
            )
            user.set_password(password)
            user.save()

            # --- Step 2: Insert into Supabase Users Table ---
            try:
                create_user_in_supabase(local_uuid, None, email, form_role)
            except Exception as se:
                print("❌ Supabase users insert failed:", se)

            # --- Step 3: Auto Login ---
            auth_user = authenticate(request, username=email, password=password)
            if auth_user:
                login(request, auth_user)
            else:
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            return redirect("profile_form", user_id=user.id)

        except Exception as e:
            messages.error(request, f"Registration error: {e}")
            return redirect(f"/register/?role={form_role}")

    return render(request, "register.html", {"role": role})


# -------------------- Login --------------------
def login_view(request):
    role = request.GET.get("role")
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            if not is_profile_complete(user):
                return redirect("profile_form", user_id=user.id)

            if user.role == "applicant":
                return redirect("dashboard_applicant")
            if user.role == "lender":
                return redirect("dashboard_lender")
        else:
            messages.error(request, "❌ Invalid email or password")
    return render(request, "login.html", {"role": role})


# -------------------- Logout --------------------
def logout_view(request):
    logout(request)
    messages.success(request, "✅ Logged out successfully")
    return redirect("/")


# -------------------- Profile Form --------------------
@login_required
def profile_form(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.user.id != user.id and not request.user.is_superuser:
        messages.error(request, "You are not allowed to edit this profile.")
        return redirect("home")

    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == "POST":
        # Basic Profile
        profile.full_name = request.POST.get("fullName")
        profile.mobile = request.POST.get("mobile")
        profile.gender = request.POST.get("gender")
        profile.marital_status = request.POST.get("maritalStatus")
        profile.address = request.POST.get("address")
        profile.pincode = request.POST.get("pincode")
        profile.city = request.POST.get("city")
        profile.state = request.POST.get("state")
        profile.pan_number = request.POST.get("panNumber")
        profile.aadhar_number = request.POST.get("aadharNumber")
        profile.save()

        # Applicant Fields
        if user.role == "applicant":
            details, _ = ApplicantDetails.objects.get_or_create(user=user)
            details.cibil_score = request.POST.get("cibilScore")
            option = request.POST.get("job_or_business")

            if option == "Job":
                details.company_name = request.POST.get("companyName")
                details.company_type = request.POST.get("companyType")
                details.designation = request.POST.get("designation")
                details.itr_job = request.POST.get("itrJob")
                details.current_salary = request.POST.get("currentSalary")
                details.other_income = request.POST.get("otherIncome")
                details.total_emi = request.POST.get("totalEmiJob")
            elif option == "Business":
                details.business_name = request.POST.get("businessName")
                details.business_type = request.POST.get("businessType")
                details.business_sector = request.POST.get("businessSector")
                details.turnover_3y = request.POST.get("turnover3y")
                details.turnover_1y = request.POST.get("turnover1y")
                details.total_emi = request.POST.get("totalEmiBusiness")
                details.itr_business = request.POST.get("itrBusiness")

            details.save()
            upsert_profile_in_supabase(user, profile, details)
            messages.success(request, "✅ Applicant profile completed successfully")
            return redirect("dashboard_applicant")

        # Lender Fields
        elif user.role == "lender":
            details, _ = LenderDetails.objects.get_or_create(user=user)
            details.lender_type = request.POST.get("lenderType")
            details.dsa_code = request.POST.get("dsaCode")
            details.firm_name = request.POST.get("firmName")
            details.gst_number = request.POST.get("gstNumber")
            details.branch_name = request.POST.get("branchName")
            details.save()
            upsert_profile_in_supabase(user, profile, details)
            messages.success(request, "✅ Lender profile completed successfully")
            return redirect("dashboard_lender")

    return render(request, "profile_form.html", {"user": user, "role": user.role.capitalize()})


# -------------------- Admin Dashboard --------------------
@login_required
def dashboard_admin(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admins only.")
        return redirect("home")

    context = {
        "applicants": ApplicantDetails.objects.all(),
        "lenders": LenderDetails.objects.all(),
        "payments": Payment.objects.all(),
        "loans": LoanRequest.objects.all(),
    }
    return render(request, "dashboard_admin.html", context)


# -------------------- Applicant & Lender Dashboards --------------------
@login_required
def dashboard_applicant(request):
    loans = LoanRequest.objects.filter(applicant=request.user)
    return render(request, "dashboard_applicant.html", {"loans": loans})


@login_required
def dashboard_lender(request):
    loans = LoanRequest.objects.all()
    return render(request, "dashboard_lender.html", {"loans": loans})


# -------------------- Dashboard Router --------------------
@login_required
def dashboard_router(request):
    role = getattr(request.user, "role", "applicant")
    if role == "lender":
        return redirect("dashboard_lender")
    return redirect("dashboard_applicant")


# -------------------- Forgot Password --------------------
def forgot_password_view(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"http://127.0.0.1:8000/reset-password/{uid}/{token}/"

            subject = "🔑 Reset your Loan Saathi Hub password"
            message = f"Hi {email},\n\nClick the link to reset your password:\n👉 {reset_link}"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
            messages.success(request, "✅ Password reset email sent.")
        except User.DoesNotExist:
            messages.error(request, "❌ Email not found.")

    return render(request, "forgot_password.html")


# -------------------- Reset Password --------------------
def reset_password_view(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "✅ Password reset successful.")
                return redirect("login")
        else:
            form = SetPasswordForm(user)
        return render(request, "reset_password.html", {"form": form})
    messages.error(request, "❌ Invalid or expired link.")
    return redirect("forgot_password")


# -------------------- Loan Request --------------------
@login_required
def loan_request(request):
    if request.method == "POST":
        # sirf applicant hi loan request bana sakta hai
        if getattr(request.user, "role", "") != "applicant":
            messages.error(request, "Only applicants can create loan requests.")
            return redirect("dashboard_router")

        loan = LoanRequest.objects.create(
            loan_id="LSH" + get_random_string(4, allowed_chars="0123456789"),
            applicant=request.user,                               # ✅ correct field
            loan_type=request.POST.get("loan_type") or "",
            amount_requested=request.POST.get("amount_requested") or 0,
            duration_months=request.POST.get("duration_months") or 0,
            interest_rate=request.POST.get("interest_rate") or 0,
            reason_for_loan=request.POST.get("reason") or None,   # ✅ correct field
        )

        # (optional) Supabase sync — safe guard with try/except
        try:
            from main.supabase_client import sync_loan_request_to_supabase
            sync_loan_request_to_supabase(loan)
        except Exception as e:
            print("Supabase sync failed:", e)

        return redirect("dashboard_router")

    return render(request, "loan_request.html")



# -------------------- Payment --------------------
@login_required
def payment_page(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    if request.method == "POST":
        payment = Payment.objects.create(
            lender=request.user,
            loan_request=loan,
            payment_method=request.POST.get("payment_method"),
            amount=request.POST.get("amount"),
            status="done",
        )
        sync_payment_to_supabase(payment)
        return redirect("dashboard_lender")

    return render(request, "payment.html", {"loan": loan})
