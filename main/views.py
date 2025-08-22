from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.utils.timezone import now
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm
import uuid

from core.supabase_client import (
    supabase,
    supabase_admin,
    create_user_in_supabase,
    upsert_profile_in_supabase,
    sync_loan_request_to_supabase,
    sync_payment_to_supabase,
)

from .models import User, Profile, ApplicantDetails, LenderDetails, LoanRequest, Payment


# -------------------- Home --------------------
def home(request):
    return render(request, "index.html")


# -------------------- Helper: profile complete? --------------------
def is_profile_complete(user):
    if not Profile.objects.filter(user=user).exists():
        return False

    if user.role == "applicant":
        return ApplicantDetails.objects.filter(user=user).exists()
    if user.role == "lender":
        return LenderDetails.objects.filter(user=user).exists()
    if user.role == "admin":
        return True
    return False


# -------------------- Register --------------------
def register_view(request):
    role = (request.GET.get("role") or "").lower()

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        form_role = (request.POST.get("role") or role or "").lower()

        if form_role not in ("applicant", "lender"):
            messages.error(request, "Please select Applicant or Lender.")
            return redirect(f"/register/?role={role or ''}")

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return redirect(f"/register/?role={form_role}")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered.")
            return redirect(f"/register/?role={form_role}")

        try:
            # Supabase signup
            auth_res = supabase.auth.sign_up({"email": email, "password": password})
            if not getattr(auth_res, "user", None):
                messages.error(request, "Supabase signup failed.")
                return redirect(f"/register/?role={form_role}")

            auth_user_id = str(auth_res.user.id)

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

            # Sync with Supabase
            create_user_in_supabase(local_uuid, auth_user_id, email, form_role)

            # Welcome email
            subject = "🎉 Welcome to Loan Saathi Hub!"
            message = f"""
Hi {email},

Thank you for registering as a {form_role.title()} 🚀
👉 Continue here: http://127.0.0.1:8000/profile/basic/{user.id}/
"""
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)

            # Auto login
            auth_user = authenticate(request, username=email, password=password)
            if auth_user:
                login(request, auth_user)
            else:
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            return redirect("basic_profile", user_id=user.id)

        except Exception as e:
            print("❌ Error during registration:", str(e))
            messages.error(request, f"Registration error: {e}")
            return redirect(f"/register/?role={form_role}")

    return render(request, "register.html", {"role": role})



# -------------------- Test Email --------------------
def send_test_email(request):
    try:
        send_mail(
            "✅ Loan Saathi Hub Test Email",
            "Hello! This is a test email 🚀",
            settings.DEFAULT_FROM_EMAIL,
            ["loansaathihub@gmail.com"],
            fail_silently=False,
        )
        return HttpResponse("✅ Test email sent successfully!")
    except Exception as e:
        return HttpResponse(f"❌ Failed to send email: {e}")


# -------------------- Login --------------------
def login_view(request):
    role = request.GET.get("role")

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)

            if not is_profile_complete(user):
                if not Profile.objects.filter(user=user).exists():
                    return redirect("basic_profile", user_id=user.id)
                if user.role == "applicant":
                    return redirect("complete_profile_applicant", user_id=user.id)
                elif user.role == "lender":
                    return redirect("complete_profile_lender", user_id=user.id)

            if user.role == "applicant":
                return redirect("dashboard_applicant")
            elif user.role == "lender":
                return redirect("dashboard_lender")

        messages.error(request, "❌ Invalid email or password")

    return render(request, "login.html", {"role": role})


# -------------------- Logout --------------------
def logout_view(request):
    logout(request)
    messages.success(request, "✅ Logged out successfully")
    return redirect("/")


# -------------------- Basic Profile --------------------
@login_required
def basic_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user.id != user.id and not request.user.is_superuser:
        messages.error(request, "You are not allowed to edit this profile.")
        return redirect("home")

    if request.method == "POST":
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.full_name = request.POST.get("full_name") or profile.full_name
        profile.dob = request.POST.get("dob") or profile.dob
        profile.marital_status = request.POST.get("marital_status") or profile.marital_status
        profile.gender = request.POST.get("gender") or profile.gender
        profile.pan_number = request.POST.get("pan_number") or profile.pan_number
        profile.aadhaar = request.POST.get("aadhaar") or profile.aadhaar
        profile.mobile = request.POST.get("mobile") or profile.mobile
        profile.address = request.POST.get("address") or profile.address
        profile.pincode = request.POST.get("pincode") or profile.pincode
        profile.city = request.POST.get("city") or profile.city
        profile.state = request.POST.get("state") or profile.state
        profile.save()

        if user.role == "applicant":
            return redirect("complete_profile_applicant", user_id=user.id)
        else:
            return redirect("complete_profile_lender", user_id=user.id)

    return render(request, "basic_profile.html", {"user": user})


# -------------------- Complete Profile Applicant --------------------
@login_required
def complete_profile_applicant(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user.id != user.id and not request.user.is_superuser:
        messages.error(request, "You are not allowed to edit this profile.")
        return redirect("home")

    if request.method == "POST":
        details, _ = ApplicantDetails.objects.get_or_create(user=user)
        details.loan_purpose = request.POST.get("loan_purpose") or details.loan_purpose
        details.employment_type = request.POST.get("employment_type") or details.employment_type
        details.job_type = request.POST.get("job_type") or details.job_type
        details.monthly_income = request.POST.get("monthly_income") or details.monthly_income
        details.other_income = request.POST.get("other_income") or details.other_income
        details.cibil_score = request.POST.get("cibil_score") or details.cibil_score
        details.itr = request.POST.get("itr") or details.itr
        details.save()

        user.role = "applicant"
        user.save()

        messages.success(request, "✅ Applicant profile completed successfully")
        return redirect("dashboard_applicant")

    return render(request, "complete_profile_applicant.html", {"user": user})


# -------------------- Complete Profile Lender --------------------
@login_required
def complete_profile_lender(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.user.id != user.id and not request.user.is_superuser:
        messages.error(request, "You are not allowed to edit this profile.")
        return redirect("home")

    if request.method == "POST":
        details, _ = LenderDetails.objects.get_or_create(user=user)
        details.business_type = request.POST.get("business_type") or details.business_type
        details.gst_number = request.POST.get("gst_number") or details.gst_number
        details.turnover = request.POST.get("turnover") or details.turnover
        details.dsa_code = request.POST.get("dsa_code") or details.dsa_code
        details.designation = request.POST.get("designation") or details.designation
        details.save()

        user.role = "lender"
        user.save()

        messages.success(request, "✅ Lender profile completed successfully")
        return redirect("dashboard_lender")

    return render(request, "complete_profile_lender.html", {"user": user})


# -------------------- Admin Dashboard --------------------
@login_required
def dashboard_admin(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admins only.")
        return redirect("home")

    applicants = ApplicantDetails.objects.all()
    lenders = LenderDetails.objects.all()
    payments = Payment.objects.all()
    loans = LoanRequest.objects.all()

    return render(request, "dashboard_admin.html", {
        "applicants": applicants,
        "lenders": lenders,
        "payments": payments,
        "loans": loans,
    })


# -------------------- Dashboards --------------------
@login_required
def dashboard_applicant(request):
    loans = LoanRequest.objects.filter(applicant=request.user)
    return render(request, "dashboard_applicant.html", {"loans": loans})


@login_required
def dashboard_lender(request):
    loans = LoanRequest.objects.all()
    return render(request, "dashboard_lender.html", {"loans": loans})


# -------------------- Dashboard Router --------------------
def dashboard_router(request):
    user_id = getattr(request, "user_id", None)
    if not user_id:
        return redirect("login")

    row = (
        supabase_admin()
        .table("main_profile")
        .select("role")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
        .data
    )
    role = (row[0]["role"] if row else "applicant")

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
            message = f"""
Hi {email},

Click the link to reset your password:
👉 {reset_link}
"""
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

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "✅ Password reset successful.")
                return redirect("login")
        else:
            form = SetPasswordForm(user)
        return render(request, "reset_password.html", {"form": form})
    else:
        messages.error(request, "❌ Invalid or expired link.")
        return redirect("forgot_password")


# -------------------- Loan Request --------------------
@login_required
def loan_request(request):
    if request.method == "POST":
        loan_type = request.POST.get("loan_type")
        amount_requested = request.POST.get("amount_requested")
        duration_months = request.POST.get("duration_months")
        interest_rate = request.POST.get("interest_rate")
        remarks = request.POST.get("remarks")

        loan_id = "LSH" + get_random_string(4, allowed_chars="0123456789")
        LoanRequest.objects.create(
            loan_id=loan_id,
            applicant=request.user,
            loan_type=loan_type,
            amount_requested=amount_requested,
            duration_months=duration_months,
            interest_rate=interest_rate,
            remarks=remarks,
        )
        return redirect("dashboard_applicant")

    return render(request, "loan_request.html")


# -------------------- Payment --------------------
@login_required
def payment_page(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    if request.method == "POST":
        Payment.objects.create(
            lender=request.user,
            loan_request=loan,
            payment_method=request.POST.get("payment_method"),
            amount=request.POST.get("amount"),
            status="done",
        )
        return redirect("dashboard_lender")

    return render(request, "payment.html", {"loan": loan})
