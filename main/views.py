from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import LoanRequest, Payment, ApplicantProfile, LenderProfile, User
from django.utils.crypto import get_random_string
from django.db.models import Q
from .supabase_client import supabase
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from django.utils.timezone import now
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm
import uuid


# -------------------- Home --------------------
def home(request):
    return render(request, "index.html")


# ------------------------
# Helper: profile complete?
# ------------------------
def is_profile_complete(applicant):
    try:
        if hasattr(applicant, "is_profile_complete"):
            return bool(getattr(applicant, "is_profile_complete"))
    except Exception:
        pass

    role = getattr(applicant, "role", "")
    if role == "applicant":
        try:
            p = applicant.applicantprofile
            return bool(p.first_name and p.mobile)
        except Exception:
            return False
    if role == "lender":
        try:
            p = applicant.lenderprofile
            return bool(p.first_name and p.mobile)
        except Exception:
            return False
    if role == "admin":
        return True
    return False


# -------------------- Register --------------------
def register_view(request):
    role = request.GET.get("role")  # Applicant / Lender

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        form_role = request.POST.get("role") or role

        try:
            print("📌 Trying Supabase signup for:", email)
            auth_res = supabase.auth.sign_up({"email": email, "password": password})
            if not auth_res.user:
                messages.error(request, "Supabase signup failed.")
                return redirect(f"/register/?role={form_role}")

            auth_user_id = str(auth_res.user.id)
            applicant_id = str(uuid.uuid4())

            supabase.table("users").insert({
                "id": applicant_id,
                "auth_user_id": auth_user_id,
                "email": email,
                "role": form_role
            }).execute()

            # ✅ Send Welcome Email
            subject = "🎉 Welcome to Loan Saathi Hub!"
            message = f"""
Hi {email},

Thank you for registering as a {form_role} with Loan Saathi Hub 🚀

We’re excited to have you on board. 
You can now log in and complete your profile to get started.

👉 Login here: http://127.0.0.1:8000/login/?role={form_role}

Cheers,  
Team Loan Saathi Hub
            """
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
                print("✅ Welcome email sent to", email)
            except Exception as e:
                print("❌ Failed to send welcome email:", str(e))

            if form_role == "Applicant":
                return redirect(f"/complete-profile/applicant/?user_id={applicant_id}")
            else:
                return redirect(f"/complete-profile/lender/?user_id={applicant_id}")

        except Exception as e:
            print("❌ Error during registration:", str(e))
            messages.error(request, f"Error: {e}")
            return redirect(f"/register/?role={form_role}")

    return render(request, "register.html", {"role": role})


# -------------------- Test Email --------------------
def send_test_email(request):
    subject = "✅ Loan Saathi Hub Test Email"
    message = "Hello! This is a test email from Loan Saathi Hub SMTP setup 🚀"
    recipient = ["loansaathihub@gmail.com"]

    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient, fail_silently=False)
        return HttpResponse("✅ Test email sent successfully!")
    except Exception as e:
        return HttpResponse(f"❌ Failed to send email: {e}")


# -------------------- Login --------------------
def login_view(request):
    role = request.GET.get("role")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)

            if not is_profile_complete(user):
                if user.role == "applicant":
                    return redirect("complete_profile_applicant")
                elif user.role == "lender":
                    return redirect("complete_profile_lender")
                elif user.role == "admin":
                    return redirect("complete_profile_admin")

            if user.role == "applicant":
                return redirect("dashboard_applicant")
            elif user.role == "lender":
                return redirect("dashboard_lender")
            elif user.role == "admin":
                return redirect("dashboard_admin")
        else:
            messages.error(request, "❌ Invalid email or password")

    return render(request, "login.html", {"role": role})


# -------------------- Logout --------------------
def logout_view(request):
    logout(request)
    messages.success(request, "✅ Logged out successfully")
    return redirect("/")


# -------------------- Dashboards --------------------
@login_required
def dashboard_applicant(request):
    loans = LoanRequest.objects.filter(user=request.user)
    return render(request, "dashboard_applicant.html", {"loans": loans})


@login_required
def dashboard_lender(request):
    loans = LoanRequest.objects.all()
    return render(request, "dashboard_lender.html", {"loans": loans})


@login_required
def dashboard_admin(request):
    return render(request, "dashboard_admin.html")
# -------------------- Forgot Password --------------------
def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"http://127.0.0.1:8000/reset-password/{uid}/{token}/"

            subject = "🔑 Reset your Loan Saathi Hub password"
            message = f"""
Hi {user.username},

We received a request to reset your password. 
Click the link below to set a new password:

👉 {reset_link}

If you didn’t request this, you can safely ignore this email.

Team Loan Saathi Hub
            """
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
            messages.success(request, "✅ Password reset email sent. Please check your inbox.")

        except User.DoesNotExist:
            messages.error(request, "❌ Email not found in our records.")

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
                messages.success(request, "✅ Your password has been reset successfully. Please log in.")
                return redirect("login")
        else:
            form = SetPasswordForm(user)
        return render(request, "reset_password.html", {"form": form})
    else:
        messages.error(request, "❌ Invalid or expired reset link.")
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
            user=request.user,
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


# -------------------- Complete Profile Applicant --------------------
@login_required
def complete_profile_applicant(request):
    if request.method == "POST":
        profile = request.user.applicantprofile

        profile.first_name = request.POST.get("firstName")
        profile.last_name = request.POST.get("lastName")
        profile.mobile = request.POST.get("mobile")
        profile.email = request.POST.get("email")
        profile.address = request.POST.get("address")
        profile.city = request.POST.get("city")
        profile.state = request.POST.get("state")
        profile.pincode = request.POST.get("pincode")
        profile.pan_number = request.POST.get("pan")
        profile.aadhaar = request.POST.get("aadhaar")
        profile.reason_for_loan = request.POST.get("reason_for_loan")
        profile.monthly_salary = request.POST.get("monthlySalary")

        profile.save()

        request.user.role = "applicant"
        request.user.is_profile_complete = True
        request.user.save()

        messages.success(request, "✅ Applicant profile completed successfully")
        return redirect("dashboard_applicant")

    return render(request, "complete_profile_applicant.html")


# -------------------- Complete Profile Lender --------------------
@login_required
def complete_profile_lender(request):
    if request.method == "POST":
        profile = request.user.lenderprofile

        profile.first_name = request.POST.get("firstName")
        profile.last_name = request.POST.get("lastName")
        profile.mobile = request.POST.get("mobile")
        profile.email = request.POST.get("email")
        profile.address = request.POST.get("address")
        profile.city = request.POST.get("city")
        profile.state = request.POST.get("state")
        profile.pincode = request.POST.get("pincode")
        profile.business_name = request.POST.get("businessName")
        profile.dsa_code = request.POST.get("dsaCode")
        profile.gst_no = request.POST.get("gstNo")

        profile.save()

        request.user.role = "lender"
        request.user.is_profile_complete = True
        request.user.save()

        messages.success(request, "✅ Lender profile completed successfully")
        return redirect("dashboard_lender")

    return render(request, "complete_profile_lender.html")


# -------------------- Complete Profile Admin --------------------
@login_required
def complete_profile_admin(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name")
        user.last_name = request.POST.get("last_name")
        user.email = request.POST.get("email")
        user.mobile = request.POST.get("mobile")
        user.role = "admin"
        user.is_staff = True
        user.is_superuser = True
        user.is_profile_complete = True
        user.save()

        messages.success(request, "✅ Admin profile completed successfully")
        return redirect("dashboard_admin")

    return render(request, "complete_profile_admin.html")


# -------------------- Admin Dashboard --------------------
@login_required
def dashboard_admin(request):
    if request.user.role != "admin":
        messages.error(request, "Access denied. Admins only.")
        return redirect("home")

    applicants = ApplicantProfile.objects.all()
    lenders = LenderProfile.objects.all()
    payments = Payment.objects.all()
    loans = LoanRequest.objects.all()

    return render(request, "admin_dashboard.html", {
        "applicants": applicants,
        "lenders": lenders,
        "payments": payments,
        "loans": loans,
    })
