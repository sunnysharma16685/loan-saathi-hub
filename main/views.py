import pdfkit
import shutil

# Auto-detect wkhtmltopdf on Render or fallback
WKHTML_PATH = shutil.which("wkhtmltopdf")
if WKHTML_PATH:
    pdfkit_config = pdfkit.configuration(wkhtmltopdf=WKHTML_PATH)
else:
    pdfkit_config = None


import os
import uuid
import json
import random
import re
import logging
import smtplib
import imaplib
import email
import requests
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    authenticate, login, logout, get_user_model
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm
from django.core.mail import send_mail
from django.db import transaction, models
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.dateparse import parse_date
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from email.mime.text import MIMEText
from dotenv import load_dotenv
import math
import razorpay
from django.views.decorators.clickjacking import xframe_options_deny
from django.utils.html import escape
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden
from django_ratelimit.decorators import ratelimit


from main.models import PaymentTransaction

# ✅ Django app imports
from main.utils import send_email_otp
from main.models import (
    User, Profile, ApplicantDetails, LenderDetails,
    LoanRequest, LoanLenderStatus, PaymentTransaction,
    SupportTicket, Complaint, Feedback, CibilReport, DeletedUserLog
)
from main.forms import (
    ApplicantRegistrationForm, LenderRegistrationForm, LoginForm,
    SupportForm, ComplaintForm, FeedbackForm
)

# ✅ Environment + Logger setup
load_dotenv()
logger = logging.getLogger(__name__)
User = get_user_model()



# -------------------- Home --------------------
def index(request): return render(request, 'index.html')

# -------------------- Profile Completion Check --------------------
def is_profile_complete(user):
    """
    Checks whether a user's profile is sufficiently complete for dashboard access.
    Includes stricter validation for both applicant and lender roles.
    """

    # ✅ Ensure valid authenticated user object
    if not user or not getattr(user, "is_authenticated", False):
        return False

    # ✅ Get or fallback to Profile
    profile = getattr(user, "profile", None) or Profile.objects.filter(user=user).first()
    if not profile:
        return False

    # ✅ Basic identity fields required for all
    if not all([
        profile.full_name,
        profile.pancard_number,
        getattr(profile, "mobile", None),
        getattr(profile, "aadhaar_number", None),
    ]):
        return False

    # ✅ Validate PAN & Aadhaar formats (extra security)
    if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", profile.pancard_number.upper()):
        return False
    if not re.match(r"^\d{12}$", str(profile.aadhaar_number)):
        return False

    # ✅ Applicant-specific completeness
    if user.role == "applicant":
        details = getattr(user, "applicantdetails", None) or ApplicantDetails.objects.filter(user=user).first()
        if not details:
            return False
        if not any([
            details.employment_type,
            details.company_name,
            details.business_name,
        ]):
            return False

    # ✅ Lender-specific completeness
    elif user.role == "lender":
        details = getattr(user, "lenderdetails", None) or LenderDetails.objects.filter(user=user).first()
        if not details:
            return False
        if not any([
            details.lender_type,
            details.bank_firm_name,
        ]):
            return False

    return True


# =====================================================
# -------------------- Register -----------------------
# =====================================================
def register_view(request):
    role = (request.GET.get("role") or "").lower()

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        confirm_password = request.POST.get("confirm_password") or ""
        form_role = (request.POST.get("role") or role).lower()

        # 🧩 Basic validation
        if form_role not in ("applicant", "lender"):
            return JsonResponse({"ok": False, "msg": "Please select applicant or lender."})
        if not email or not password:
            return JsonResponse({"ok": False, "msg": "Email and password are required."})
        if password != confirm_password:
            return JsonResponse({"ok": False, "msg": "Passwords do not match."})
        if User.objects.filter(email=email).exists():
            return JsonResponse({"ok": False, "msg": "Email already registered."})

        # 🧠 Send OTP via email
        try:
            otp_data = send_email_otp(email)

            if otp_data.get("ok"):
                request.session.update({
                    "reg_email": email,
                    "reg_password": make_password(password),
                    "reg_role": form_role,
                    "otp": otp_data["otp"],
                    "otp_email": email,
                    "otp_expiry": (timezone.now() + timedelta(minutes=5)).isoformat()
                })
                return JsonResponse({"ok": True, "show_otp": True, "msg": "OTP sent to your email."})

            # 🚨 If sending fails
            logger.warning(f"⚠️ OTP send failed for {email}: {otp_data}")
            return JsonResponse({"ok": False, "msg": "Failed to send OTP. Please try again."})

        except Exception as e:
            logger.exception(f"Registration error for {email}: {e}")
            return JsonResponse({"ok": False, "msg": "Unexpected error during registration. Try again later."})

    # GET → Render registration page
    return render(request, "register.html", {"role": role})


# -------------------- Login --------------------
def login_view(request):
    role = (request.GET.get("role") or "").lower()
    email_val = (request.POST.get("email") or "").strip().lower() if request.method == "POST" else ""

    if request.method == "POST":
        password = request.POST.get("password") or ""
        form_role = (request.POST.get("role") or role).lower()

        # Try authentication with email or username
        user = (
            authenticate(request, email=email_val, password=password)
            or authenticate(request, username=email_val, password=password)
        )

        if not user:
            messages.error(request, "❌ Invalid email or password.")
            return redirect(f"/login/?role={form_role}")

        # Superuser shortcut
        if user.is_superuser:
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("dashboard_router")

        # Role mismatch check
        if form_role and user.role and user.role != form_role:
            messages.error(request, "❌ Role mismatch.")
            return redirect(f"/login/?role={form_role}")

        profile = getattr(user, "profile", None)
        if not profile:
            messages.error(request, "⚠️ Profile not found.")
            return redirect("login")

        # Status checks
        status = getattr(profile, "status", None)
        if status == "Hold":
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("review_profile")

        if status in ["Deactivated", "Deleted"]:
            messages.error(request, f"🚫 Your profile is {status}.")
            return redirect("login")

        if status != "Active":
            messages.error(request, "⚠️ Profile not active.")
            return redirect("login")

        # Final login
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

        # Redirect if profile incomplete
        if not getattr(profile, "full_name", None):
            return redirect("profile_form", user_id=str(user.id))

        return redirect("dashboard_router")

    # GET request → login page
    return render(request, "login.html", {"role": role, "email": email_val})

# -------------------- Logout --------------------
def logout_view(request):
    logout(request)
    messages.success(request,"✅ Logged out successfully")
    return redirect("/")

# -------------------- OTP Verify + Resend --------------------
def verify_email_otp_view(request):
    user_otp = (request.GET.get("otp") or "").strip()
    session_otp = request.session.get("otp")
    expiry_str = request.session.get("otp_expiry")
    expiry = datetime.fromisoformat(expiry_str) if expiry_str else None
    if not session_otp or not expiry: return JsonResponse({"ok": False, "msg": "OTP not found or expired."})
    if timezone.now() > expiry: return JsonResponse({"ok": False, "msg": "OTP expired."})
    if user_otp != str(session_otp): return JsonResponse({"ok": False, "msg": "Invalid OTP."})
    email, password_hash, role = request.session.get("reg_email"), request.session.get("reg_password"), request.session.get("reg_role")
    if not email or not password_hash or not role:
        return JsonResponse({"ok": False, "msg": "Session expired. Please register again."})
    user = User(email=email, role=role, is_active=True); user.password=password_hash; user.save()
    login(request,user,backend="django.contrib.auth.backends.ModelBackend")
    for k in ("otp","otp_email","otp_user_id","otp_expiry","reg_email","reg_password","reg_role"): request.session.pop(k,None)
    return JsonResponse({"ok":True,"msg":"OTP verified!","redirect_url":reverse("profile_form",args=[str(user.id)])})

def resend_email_otp_view(request):
    email = request.session.get("reg_email")
    if not email: return JsonResponse({"ok":False,"msg":"Session expired. Please register again."})
    otp_data = send_email_otp(email)
    if otp_data.get("ok"):
        request.session["otp"]=otp_data["otp"]; request.session["otp_email"]=email
        request.session["otp_expiry"]=(timezone.now()+timedelta(minutes=5)).isoformat()
        return JsonResponse({"ok":True,"msg":"New OTP sent"})
    return JsonResponse({"ok":False,"msg":"Failed to resend OTP"})

# -------------------- Profile Form --------------------
@login_required
def profile_form(request, user_id):
    logger.error("🔎 Entered profile_form for user_id=%s by %s", user_id, request.user.email)
    user = get_object_or_404(User, id=user_id)

    # ✅ Prevent unauthorized edit
    if request.user.id != user.id and not request.user.is_superuser:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errors": {"auth": ["Access denied."]}}, status=403)
        messages.error(request, "You are not allowed to edit this profile.")
        return redirect("index")

    role = (user.role or "").lower()

    # ✅ Ensure profile exists with defaults
    profile, created = Profile.objects.get_or_create(
        user=user,
        defaults={
            "full_name": user.email.split("@")[0],
            "status": "Hold",
            "pancard_number": f"DUMMY{uuid.uuid4().hex[:4].upper()}X",
            "aadhaar_number": str(random.randint(10**11, 10**12 - 1)).zfill(12),
        },
    )

    applicant_details = ApplicantDetails.objects.filter(user=user).first() if role == "applicant" else None
    lender_details = LenderDetails.objects.filter(user=user).first() if role == "lender" else None

    def G(*keys):
        for k in keys:
            v = request.POST.get(k)
            if v and str(v).strip():
                return str(v).strip()
        return None

    if request.method == "POST":
        errors, warnings = {}, []

        # ✅ PAN validation
        pancard_number = G("pancard_number", "panCardNumber")
        if not pancard_number:
            errors["pancard_number"] = ["PAN Card Number is required."]
        elif not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pancard_number.upper()):
            errors["pancard_number"] = ["Invalid PAN format. Example: ABCDE1234F"]
        elif Profile.objects.filter(pancard_number=pancard_number.upper()).exclude(user=user).exists():
            errors["pancard_number"] = [f"PAN {pancard_number} already exists."]

        # ✅ Aadhaar validation
        aadhaar_number = G("aadhaar_number", "aadhaarNumber")
        aadhaar_clean = aadhaar_number.replace(" ", "") if aadhaar_number else None
        if not aadhaar_clean:
            errors["aadhaar_number"] = ["Aadhaar Number is required."]
        elif not re.match(r"^\d{12}$", aadhaar_clean):
            errors["aadhaar_number"] = ["Invalid Aadhaar format. Must be exactly 12 digits."]
        elif Profile.objects.filter(aadhaar_number=aadhaar_clean).exclude(user=user).exists():
            errors["aadhaar_number"] = [f"Aadhaar {aadhaar_clean} already exists."]

        # ✅ Optional warnings
        optional_fields = ["gender", "marital_status", "address", "pincode", "city", "state"]
        for f in optional_fields:
            if not G(f):
                warnings.append(f)

        # ❌ Errors → return immediately
        if errors:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "errors": errors, "warnings": warnings})
            for field, msgs in errors.items():
                for msg in msgs:
                    messages.error(request, msg)
            return render(request, "profile_form.html", {
                "user": user, "profile": profile, "role": role.capitalize(),
                "applicant_details": applicant_details, "lender_details": lender_details, "errors": errors
            })

        # ✅ Save Profile
        profile.full_name = G("full_name", "fullName") or profile.full_name
        profile.mobile = G("mobile") or profile.mobile
        dob_val = G("dob")
        profile.dob = parse_date(dob_val) if dob_val else profile.dob
        profile.gender = G("gender") or profile.gender
        profile.marital_status = G("marital_status", "maritalStatus") or profile.marital_status
        profile.address = G("address") or profile.address
        profile.pincode = G("pincode") or profile.pincode
        profile.city = G("city") or profile.city
        profile.state = G("state") or profile.state
        profile.pancard_number = pancard_number.upper()
        profile.aadhaar_number = aadhaar_clean
        profile.save()

        # ✅ Applicant / Lender Details
        if role == "applicant":
            details, _ = ApplicantDetails.objects.get_or_create(user=user)
            details.employment_type = G("employment_type") or details.employment_type
            cibil_val = G("cibil_score")
            details.cibil_score = int(cibil_val) if cibil_val and cibil_val.isdigit() else details.cibil_score
            details.company_name = G("company_name") or details.company_name
            details.company_type = G("company_type") or details.company_type
            details.designation = G("designation") or details.designation
            details.itr = G("itr") or details.itr
            details.current_salary = G("current_salary") or details.current_salary
            details.other_income = G("other_income") or details.other_income
            details.total_emi = G("total_emi") or details.total_emi
            details.business_name = G("business_name") or details.business_name
            details.business_type = G("business_type") or details.business_type
            details.business_sector = G("business_sector") or details.business_sector
            details.total_turnover = G("total_turnover") or details.total_turnover
            details.last_year_turnover = G("last_year_turnover") or details.last_year_turnover
            details.business_total_emi = G("business_total_emi") or details.business_total_emi
            details.business_itr_status = G("business_itr_status") or details.business_itr_status
            details.save()

        elif role == "lender":
            l, _ = LenderDetails.objects.get_or_create(user=user)
            l.lender_type = G("lender_type") or l.lender_type
            l.bank_firm_name = G("bank_firm_name") or l.bank_firm_name
            l.branch_name = G("branch_name") or l.branch_name
            l.dsa_code = G("dsa_code") or l.dsa_code
            l.designation = G("designation") or l.designation
            l.gst_number = G("gst_number") or l.gst_number
            l.save()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "redirect_url": reverse("review_profile"), "warnings": warnings})

        if warnings:
            for w in warnings:
                messages.warning(request, f"{w.capitalize()} is recommended but not filled.")
        messages.success(request, "✅ Profile saved successfully.")
        return redirect("review_profile")

    return render(request, "profile_form.html", {
        "user": user, "profile": profile, "role": role.capitalize(),
        "applicant_details": applicant_details, "lender_details": lender_details
    })


# -------------------- Edit Profile --------------------
@login_required
def edit_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # ✅ Access control
    if request.user.id != user.id and not request.user.is_superuser:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errors": {"auth": ["Access denied."]}}, status=403)
        messages.error(request, "You are not allowed to edit this profile.")
        return redirect("index")

    role = (user.role or "").lower()
    profile, _ = Profile.objects.get_or_create(user=user)
    applicant_details = ApplicantDetails.objects.filter(user=user).first() if role == "applicant" else None
    lender_details = LenderDetails.objects.filter(user=user).first() if role == "lender" else None

    def G(*keys):
        for k in keys:
            v = request.POST.get(k)
            if v and str(v).strip():
                return str(v).strip()
        return None

    if request.method == "POST":
        errors, warnings = {}, []

        # PAN/Aadhaar are locked — only validation
        if not profile.pancard_number or not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", profile.pancard_number.upper()):
            errors["pancard_number"] = ["Invalid PAN format."]
        if not profile.aadhaar_number or not re.match(r"^\d{12}$", profile.aadhaar_number):
            errors["aadhaar_number"] = ["Invalid Aadhaar format."]

        optional_fields = ["gender", "marital_status", "address", "pincode", "city", "state"]
        for f in optional_fields:
            if not G(f):
                warnings.append(f)

        if errors:
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "errors": errors, "warnings": warnings})
            for field, msgs in errors.items():
                for msg in msgs:
                    messages.error(request, msg)
            return render(request, "edit_profile.html", {
                "user": user, "profile": profile, "role": role.capitalize(),
                "applicant_details": applicant_details, "lender_details": lender_details,
                "errors": errors, "dashboard_url": reverse("dashboard_applicant") if role == "applicant" else reverse("dashboard_lender"),
            })

        # Save editable fields only
        profile.gender = G("gender") or profile.gender
        profile.marital_status = G("marital_status") or profile.marital_status
        profile.address = G("address") or profile.address
        profile.pincode = G("pincode") or profile.pincode
        profile.city = G("city") or profile.city
        profile.state = G("state") or profile.state
        profile.save()

        if role == "applicant" and applicant_details:
            applicant_details.employment_type = G("employment_type") or applicant_details.employment_type
            cibil_val = G("cibil_score")
            applicant_details.cibil_score = int(cibil_val) if cibil_val and cibil_val.isdigit() else applicant_details.cibil_score
            applicant_details.company_name = G("company_name") or applicant_details.company_name
            applicant_details.company_type = G("company_type") or applicant_details.company_type
            applicant_details.designation = G("designation") or applicant_details.designation
            applicant_details.itr = G("itr") or applicant_details.itr
            applicant_details.current_salary = G("current_salary") or applicant_details.current_salary
            applicant_details.other_income = G("other_income") or applicant_details.other_income
            applicant_details.total_emi = G("total_emi") or applicant_details.total_emi
            applicant_details.business_name = G("business_name") or applicant_details.business_name
            applicant_details.business_type = G("business_type") or applicant_details.business_type
            applicant_details.business_sector = G("business_sector") or applicant_details.business_sector
            applicant_details.total_turnover = G("total_turnover") or applicant_details.total_turnover
            applicant_details.last_year_turnover = G("last_year_turnover") or applicant_details.last_year_turnover
            applicant_details.business_total_emi = G("business_total_emi") or applicant_details.business_total_emi
            applicant_details.business_itr_status = G("business_itr_status") or applicant_details.business_itr_status
            applicant_details.save()
            messages.success(request, "✅ Applicant profile updated successfully!")

        elif role == "lender" and lender_details:
            lender_details.lender_type = G("lender_type") or lender_details.lender_type
            lender_details.bank_firm_name = G("bank_firm_name") or lender_details.bank_firm_name
            lender_details.branch_name = G("branch_name") or lender_details.branch_name
            lender_details.dsa_code = G("dsa_code") or lender_details.dsa_code
            lender_details.designation = G("designation") or lender_details.designation
            lender_details.gst_number = G("gst_number") or lender_details.gst_number
            lender_details.save()
            messages.success(request, "✅ Lender profile updated successfully!")

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "redirect_url": reverse("edit_profile", args=[user.id]), "warnings": warnings})

        return redirect("edit_profile", user_id=user.id)

    return render(request, "edit_profile.html", {
        "user": user, "profile": profile, "role": role.capitalize(),
        "applicant_details": applicant_details, "lender_details": lender_details,
        "dashboard_url": reverse("dashboard_applicant") if role == "applicant" else reverse("dashboard_lender"),
    })


# -------------------- Review Profile (Applicant & Lender)--------------------
@login_required
def review_profile(request):
    return render(request, "review_profile.html")

# -------------------- Admin Login --------------------
def admin_login(request):
    if request.method=="POST":
        identifier=(request.POST.get("identifier") or "").strip()
        password=(request.POST.get("password") or "").strip()
        user=(User.objects.filter(email__iexact=identifier).first()
              or User.objects.filter(profile__mobile=identifier).first())
        if user:
            auth_user=authenticate(request,email=user.email,password=password)
            if auth_user and auth_user.is_superuser:
                login(request,auth_user); return redirect("dashboard_admin")
        messages.error(request,"❌ Invalid admin credentials")
    return render(request,"admin_login.html")

# -------------------- Admin Logout --------------------
@login_required
def admin_logout(request):
    logout(request)
    messages.success(request, "✅ Admin logged out successfully")
    return redirect("admin_login")

# -------------------- Admin Dashboard --------------------
@login_required
def dashboard_admin(request):
    if not request.user.is_superuser:
        messages.error(request, "Admins only.")
        return redirect("index")

    # ✅ Users / Applicants / Lenders / Loans / Payments
    users_qs = User.objects.select_related("profile").all().order_by("-created_at")
    applicants = ApplicantDetails.objects.select_related("user", "user__profile").all().order_by("-id")
    lenders = LenderDetails.objects.select_related("user", "user__profile").all().order_by("-id")
    loans = LoanRequest.objects.select_related("applicant", "accepted_lender").all().order_by("-created_at")
    payments = (
        PaymentTransaction.objects.select_related("user", "user__profile")
        .all()
        .order_by("-created_at")
    )

    # ✅ Decorated Users (with deleted log email fix)
    decorated_users = []
    for u in users_qs:
        profile = getattr(u, "profile", None)
        status = getattr(profile, "status", "No Profile") if profile else "No Profile"
        delete_reason = getattr(profile, "delete_reason", None) if profile else None

        # 🛠 Fix: Show actual email from DeletedUserLog (if deleted)
        display_email = u.email
        if status == "Deleted":
            last_log = (
                DeletedUserLog.objects.filter(mobile=getattr(profile, "mobile", None))
                .order_by("-deleted_at")
                .first()
            )
            if last_log and last_log.email:
                display_email = last_log.email

        decorated_users.append({
            "obj": u,
            "profile": profile,
            "status": status,
            "display_email": display_email,
            "delete_reason": delete_reason or "No reason provided",
            "can_delete": status not in ["Deleted", "No Profile"],
        })

    # ✅ Gmail Integration (Unread count + last 5 mails latest first)
    mails, unread_count = [], 0
    try:
        import imaplib, email
        from email.header import decode_header

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        mail.select("inbox")

        # Count unread mails
        status, response = mail.search(None, "UNSEEN")
        if status == "OK" and response[0]:
            unread_count = len(response[0].split())

        # Fetch last 5 mails (latest first)
        status, data = mail.search(None, "ALL")
        if status == "OK" and data[0]:
            ids = data[0].split()
            for num in reversed(ids[-5:]):  # latest first
                _, raw = mail.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(raw[0][1])

                # Decode subject safely
                subject, encoding = decode_header(msg.get("Subject"))[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8", errors="ignore")

                # Extract snippet
                snippet = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        disp = str(part.get("Content-Disposition"))
                        if ctype == "text/plain" and "attachment" not in disp:
                            snippet = part.get_payload(decode=True).decode(errors="ignore")[:120]
                            break
                        elif ctype == "text/html" and not snippet:
                            snippet = part.get_payload(decode=True).decode(errors="ignore")[:120]
                else:
                    snippet = msg.get_payload(decode=True).decode(errors="ignore")[:120]

                mails.append({
                    "from": msg.get("From"),
                    "to": msg.get("To"),
                    "subject": subject,
                    "date": msg.get("Date"),
                    "snippet": snippet.strip(),
                })

        mail.logout()

    except Exception as e:
        logger.error(f"📧 Gmail fetch error: {e}")
        mails = [{"from": "Error", "subject": "Email fetch failed", "date": "", "snippet": str(e)}]

    # ✅ Razorpay-specific data (aggregated summary)
    total_completed = payments.filter(status="Completed").count()
    total_pending = payments.filter(status="Pending").count()
    total_failed = payments.filter(status="Failed").count()
    total_revenue = payments.filter(status="Completed").aggregate(
        total=models.Sum("amount")
    )["total"] or 0

    # ✅ Context
    context = {
        "users_dec": decorated_users,
        "users": users_qs,
        "applicants": applicants,
        "lenders": lenders,
        "loans": loans,
        "payments": payments,
        "unread_mails_count": unread_count,
        "mails": mails,
        "razorpay_summary": {
            "total_completed": total_completed,
            "total_pending": total_pending,
            "total_failed": total_failed,
            "total_revenue": total_revenue,
        },
    }

    # ✅ Final Render
    return render(request, "dashboard_admin.html", context)


# -------------------- Admin View Profile --------------------
from django.db.models import Q

@login_required
def admin_view_profile(request, user_id):
    if not request.user.is_superuser:
        return redirect("dashboard_admin")

    # ✅ User with Profile
    user = get_object_or_404(User.objects.select_related("profile"), id=user_id)
    profile = getattr(user, "profile", None)

    # ✅ Role mapping
    applicant = ApplicantDetails.objects.filter(user=user).first() if user.role == "applicant" else None
    lender = LenderDetails.objects.filter(user=user).first() if user.role == "lender" else None

    # ✅ Deleted log check (multi-key match)
    deleted_log = None
    if profile:
        deleted_log = (
            DeletedUserLog.objects.filter(
                Q(email=user.email) |
                Q(mobile=getattr(profile, "mobile", None)) |
                Q(pancard_number=getattr(profile, "pancard_number", None)) |
                Q(aadhaar_number=getattr(profile, "aadhaar_number", None))
            )
            .order_by("-deleted_at")
            .first()
        )

    # ✅ Display email fix
    display_email = user.email
    if profile and profile.status == "Deleted" and deleted_log and deleted_log.email:
        display_email = deleted_log.email

    return render(
        request,
        "admin_full_profile.html",
        {
            "user": user,
            "profile": profile,
            "applicant_details": applicant,
            "lender_details": lender,
            "deleted_log": deleted_log,
            "display_email": display_email,
        }
    )
# -------------------- Admin Actions --------------------
@login_required
@require_http_methods(["POST"])
@csrf_protect
def admin_user_action(request, user_id):
    if not request.user.is_superuser:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "msg": "🚫 Access denied."}, status=403)
        return redirect("dashboard_admin")

    action = (request.POST.get("action") or "").lower()
    reason = (request.POST.get("reason") or "").strip()[:1000]

    try:
        target = User.objects.select_related("profile").get(id=user_id)
    except User.DoesNotExist:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "msg": "❌ User not found."}, status=404)
        messages.error(request, "❌ User not found.")
        return redirect("dashboard_admin")

    profile = getattr(target, "profile", None)
    orig_email = target.email

    try:
        with transaction.atomic():
            if action == "accept":
                if profile:
                    profile.status = "Active"
                    profile.is_reviewed = True
                    profile.save()
                target.is_active = True
                target.save()
                msg = "✅ User approved"

            elif action == "deactivate":
                target.is_active = False
                target.save()
                if profile:
                    profile.status = "Deactivated"
                    profile.is_blocked = True
                    profile.save()
                msg = "⚠️ User deactivated"

            elif action == "activate":
                target.is_active = True
                target.save()
                if profile:
                    profile.status = "Active"
                    profile.is_blocked = False
                    profile.save()
                msg = "✅ User re-activated"

            elif action == "delete":
                if not reason:
                    if request.headers.get("x-requested-with") == "XMLHttpRequest":
                        return JsonResponse({"ok": False, "msg": "❌ Reason required."})
                    messages.error(request, "❌ Reason required")
                    return redirect("dashboard_admin")

                # ✅ Save original email & reason in DeletedUserLog
                DeletedUserLog.objects.create(
                    email=orig_email,
                    mobile=getattr(profile, "mobile", None),
                    pancard_number=getattr(profile, "pancard_number", None),
                    aadhaar_number=getattr(profile, "aadhaar_number", None),
                    reason=reason,
                )

                # Mask user account (login रोकने के लिए, लेकिन नया register allow रहेगा)
                target.is_active = False
                target.email = f"disabled+{target.id}@blocked.loansaathihub"
                target.username = f"disabled_{target.id}"
                target.save()

                if profile:
                    profile.status = "Deleted"
                    profile.is_blocked = True
                    profile.save()

                msg = "🗑️ User deleted"

            else:
                msg = "❌ Unknown action"

        # ✅ Return JSON for AJAX or redirect for normal
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": True, "msg": msg})
        messages.success(request, msg)
        return redirect("dashboard_admin")

    except Exception as e:
        logger.exception("Admin action failed: %s", e)
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "msg": f"⚠️ Error: {e}"})
        messages.error(request, f"⚠️ Error: {e}")
        return redirect("dashboard_admin")

# -------------------- Dashboard Router --------------------
@login_required
def dashboard_router(request):
    if request.user.is_superuser:
        return redirect("dashboard_admin")
    role=getattr(request.user,"role",None)
    profile=getattr(request.user,"profile",None)
    if profile and not profile.is_reviewed:
        return render(request,"review_profile.html",{"profile":profile})
    if role=="lender": return redirect("dashboard_lender")
    if role=="applicant": return redirect("dashboard_applicant")
    return redirect("index")

# -------------------- Applicant Dashboard (Manual Finalisation Fixed) --------------------
@login_required
def dashboard_applicant(request):
    profile = getattr(request.user, "profile", None)
    if profile and not profile.is_reviewed:
        return render(request, "review_profile.html", {"profile": profile})

    loans = (
        LoanRequest.objects.filter(applicant=request.user)
        .prefetch_related("lender_statuses", "accepted_lender")
        .order_by("-created_at")
    )
    today = date.today()

    for loan in loans:
        statuses = list(loan.lender_statuses.all()) if hasattr(loan, "lender_statuses") else []
        approved_lenders = [ls for ls in statuses if ls.status == "Approved"]
        rejected_lenders = [ls for ls in statuses if ls.status == "Rejected"]

        # 🧩 1️⃣: If applicant has manually accepted a lender (manual finalisation)
        if loan.status == "Finalised" and loan.accepted_lender:
            loan.global_status = "Finalised"
            loan.global_remarks = f"✅ You finalised {loan.accepted_lender.profile.full_name or 'the lender'}."
            continue

        # 🧩 2️⃣: Lender(s) approved, but applicant hasn’t finalised yet
        if approved_lenders and loan.status in ["Pending", "AutoApproved", "Accepted"]:
            loan.global_status = "Approved"
            loan.global_remarks = f"✅ {len(approved_lenders)} lender(s) approved your loan. Please review and choose one."
            continue

        # 🧩 3️⃣: No lender response yet
        if not statuses or all(ls.status == "Pending" for ls in statuses):
            loan.global_status = "Pending"
            loan.global_remarks = "⌛ Awaiting lender responses."
            continue

        # 🧩 4️⃣: All lenders rejected
        if len(rejected_lenders) == len(statuses):
            loan.global_status = "Rejected"
            loan.global_remarks = "❌ All lenders rejected your loan."
            continue

        # 🧩 5️⃣: In review
        loan.global_status = "Pending"
        loan.global_remarks = "⌛ Lenders are reviewing your loan."

    total_today = loans.filter(created_at__date=today).count()
    total_approved = sum(1 for loan in loans if loan.global_status == "Approved")
    total_rejected = sum(1 for loan in loans if loan.global_status == "Rejected")
    total_pending = sum(1 for loan in loans if loan.global_status == "Pending")

    context = {
        "loans": loans,
        "total_today": total_today,
        "total_approved": total_approved,
        "total_rejected": total_rejected,
        "total_pending": total_pending,
    }
    return render(request, "dashboard_applicant.html", context)



# -------------------- Lender Dashboard --------------------
@login_required
def dashboard_lender(request):
    user = request.user
    profile = getattr(user, "profile", None)

    # ✅ Step 1: Block until admin approves
    if profile and not profile.is_reviewed:
        return render(request, "review_profile.html", {"profile": profile})

    # ✅ Step 2: Fetch all feedbacks for this lender
    lender_feedbacks = (
        LoanLenderStatus.objects.filter(lender=user)
        .select_related("loan", "loan__applicant")
        .order_by("-updated_at")
    )

    # ✅ Step 3: Annotate each feedback with enhanced display logic
    for fb in lender_feedbacks:
        loan = fb.loan

        # -------------------------
        # 🌐 Unified Display Logic
        # -------------------------
        if loan.status == "Accepted" and loan.accepted_lender == user:
            # Applicant finalised this lender
            fb.display_status = "Finalised"
            fb.loan.global_status = "Approved"

        elif loan.status == "Accepted" and loan.accepted_lender != user:
            # Applicant finalised another lender
            fb.display_status = "Closed"
            fb.loan.global_status = "Rejected"

        elif loan.status == "Finalised":
            # Loan completely closed off
            fb.display_status = "Closed"
            fb.loan.global_status = "Rejected"

        elif fb.status == "Approved":
            # Lender approved the request; awaiting applicant
            fb.display_status = "Approved"
            fb.loan.global_status = "Approved"

        elif fb.status == "Rejected":
            fb.display_status = "Rejected"
            fb.loan.global_status = "Rejected"

        else:
            fb.display_status = "Pending"
            fb.loan.global_status = "Pending"

        # ✅ Step 3A: Payment check per loan
        payment = (
            PaymentTransaction.objects.filter(
                user=user,
                loan_request=loan,
                status="Completed"
            )
            .order_by("-created_at")
            .first()
        )

        fb.payment_done = bool(payment)
        fb.payment_txn = payment.txn_id if payment else None

        # ✅ Step 3B: Mark Approved if payment done but still pending
        if fb.payment_done and fb.display_status == "Pending":
            fb.display_status = "Approved"
            fb.loan.global_status = "Approved"

    # ✅ Step 4: Dashboard counts (updated with new states)
    today = timezone.now().date()
    total_today = lender_feedbacks.filter(loan__created_at__date=today).count()
    total_approved = sum(1 for fb in lender_feedbacks if fb.display_status == "Approved")
    total_rejected = sum(1 for fb in lender_feedbacks if fb.display_status == "Rejected")
    total_pending = sum(1 for fb in lender_feedbacks if fb.display_status == "Pending")

    # ✅ Step 5: Pending and finalised loan sections
    handled_loans = LoanLenderStatus.objects.filter(lender=user).values_list("loan_id", flat=True)
    pending_loans = (
        LoanRequest.objects.filter(status="Pending", accepted_lender__isnull=True)
        .exclude(id__in=handled_loans)
        .select_related("applicant")
        .order_by("-created_at")
    )
    finalised_loans = (
        LoanRequest.objects.filter(status__in=["Accepted", "Finalised"])
        .select_related("applicant", "accepted_lender")
    )

    # ✅ Step 6: Render everything
    context = {
        "profile": profile,
        "lender_feedbacks": lender_feedbacks,
        "total_today": total_today,
        "total_approved": total_approved,
        "total_rejected": total_rejected,
        "total_pending": total_pending,
        "pending_loans": pending_loans,
        "finalised_loans": finalised_loans,
    }

    return render(request, "dashboard_lender.html", context)


# -------------------- Applicant Accept Loan --------------------
@login_required
@require_POST
def applicant_accept_loan(request, loan_id, lender_id):
    try:
        loan = get_object_or_404(LoanRequest, id=loan_id, applicant=request.user)
        lender = get_object_or_404(User, id=lender_id, is_lender=True)

        # ✅ Ensure lender approved this loan
        if not LoanLenderStatus.objects.filter(loan=loan, lender=lender, status="Approved").exists():
            return JsonResponse({
                "ok": False,
                "msg": "This lender has not approved your loan yet."
            }, status=400)

        # ✅ Prevent duplicate finalisation
        if loan.status == "Finalised" and loan.accepted_lender:
            return JsonResponse({
                "ok": False,
                "msg": f"You already finalised {loan.accepted_lender.profile.full_name or 'another lender'}."
            }, status=400)

        # ✅ Finalise this loan manually
        loan.accepted_lender = lender
        loan.status = "Finalised"
        loan.save(update_fields=["accepted_lender", "status"])

        # ✅ Lock other lenders
        LoanLenderStatus.objects.exclude(lender=lender).filter(loan=loan).update(status="Finalised")

        return JsonResponse({
            "ok": True,
            "msg": f"🎉 You have finalised {lender.profile.full_name or 'this lender'}.",
            "lender_name": lender.profile.full_name or "Selected Lender"
        })

    except Exception as e:
        # Always return clean JSON error
        return JsonResponse({"ok": False, "msg": f"Server error: {str(e)}"}, status=500)


# -------------------- Loan Request --------------------
@login_required
def loan_request(request):
    if request.method=="POST" and request.user.role=="applicant":
        loan_id="LSH"+get_random_string(6,allowed_chars="0123456789")
        loan=LoanRequest.objects.create(
            id=uuid.uuid4(),loan_id=loan_id,applicant=request.user,
            loan_type=request.POST.get("loan_type") or "",
            amount_requested=request.POST.get("amount_requested") or 0,
            duration_months=request.POST.get("duration_months") or 0,
            interest_rate=request.POST.get("interest_rate") or 0,
            reason_for_loan=request.POST.get("reason_for_loan") or "",status="Pending")
        for lender in User.objects.filter(role="lender"):
            LoanLenderStatus.objects.create(loan=loan,lender=lender,status="Pending",remarks="Lender Reviewing")
        messages.success(request,f"✅ Loan {loan.loan_id} submitted.")
        return redirect("dashboard_router")
    return render(request,"loan_request.html")

# -------------------- Lender Approve / Reject Loan --------------------
@login_required
def reject_loan(request,loan_id):
    if request.method=="POST":
        reason=request.POST.get("reason")
        loan=get_object_or_404(LoanRequest,id=loan_id)
        lender_status=get_object_or_404(LoanLenderStatus,loan=loan,lender=request.user)
        lender_status.status,lender_status.remarks="Rejected",reason; lender_status.save()
        messages.warning(request,f"Loan {loan.loan_id} rejected: {reason}")
        return redirect("dashboard_lender")

@login_required
def approve_loan(request,loan_id):
    ls=get_object_or_404(LoanLenderStatus,loan__id=loan_id,lender=request.user)
    ls.status,ls.remarks="Approved","Payment done, Loan Approved"; ls.save()
    messages.success(request,f"Loan {ls.loan.loan_id} approved.")
    return redirect("dashboard_lender")


# ---------------------------------------------------------------------
# ✅ Step 1: Initiate Razorpay Payment (₹49 fixed, includes 18% GST)
# ---------------------------------------------------------------------
@login_required
@csrf_exempt
def initiate_payment(request):
    """
    Initiates a Razorpay payment for ₹49 (inclusive of 18% GST).
    """
    if request.method == "POST":
        try:
            user = request.user

            # Fixed pricing details
            total_amount = Decimal("49.00")
            base_amount = (total_amount / Decimal("1.18")).quantize(Decimal("0.01"))
            gst_amount = (total_amount - base_amount).quantize(Decimal("0.01"))
            amount_paise = int(total_amount * 100)
            merchant_order_id = f"ORD-{user.id}-{uuid.uuid4().hex[:8].upper()}"

            # ✅ Razorpay Client (LIVE keys loaded from Render environment)
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.set_app_details({"title": "Loan Saathi Hub", "version": "1.0"})

            # ✅ Create order on Razorpay
            order = client.order.create({
                "amount": amount_paise,
                "currency": "INR",
                "receipt": merchant_order_id[:40],
                "payment_capture": 1,
            })

            # ✅ Save order locally
            with transaction.atomic():
                PaymentTransaction.objects.create(
                    user=user,
                    txn_id=order["id"],
                    amount=total_amount,
                    status="Pending",
                    payment_method="Razorpay",
                )

            mode = "Live" if settings.RAZORPAY_KEY_ID.startswith("rzp_live") else "Test"
            logger.info(f"✅ Razorpay order created ({mode}) | ₹{total_amount} | User={user.email}")

            return JsonResponse({
                "ok": True,
                "order_id": order["id"],
                "amount": amount_paise,
                "currency": "INR",
                "key": settings.RAZORPAY_KEY_ID,
                "base_amount": str(base_amount),
                "gst_amount": str(gst_amount),
                "gst_percent": "18%",
            })

        except razorpay.errors.BadRequestError as e:
            logger.error(f"❌ Razorpay API BadRequestError: {e}", exc_info=True)
            return JsonResponse({"ok": False, "error": "Invalid payment request."}, status=400)

        except Exception as e:
            logger.error(f"❌ Payment initiation failed: {e}", exc_info=True)
            return JsonResponse({"ok": False, "error": str(e)}, status=400)

    return render(request, "payments/initiate_payment.html")


# ---------------------------------------------------------------------
# ✅ Step 2: Razorpay Callback / Verification (Final Polished Version)
# ---------------------------------------------------------------------
@csrf_exempt
def payment_callback(request):
    """
    Verify Razorpay payment signature, update transaction,
    and sync lender/applicant loan statuses (auto-approve lender feedback).
    """
    try:
        data = request.POST
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature")
        loan_id = data.get("loan_id")  # ✅ Sent from front-end JS handler

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            logger.warning("⚠️ Incomplete Razorpay callback data received.")
            return JsonResponse({"ok": False, "error": "Incomplete payment data"}, status=400)

        # ✅ Verify Razorpay signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        verified = True
        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
        except razorpay.errors.SignatureVerificationError:
            verified = False

        # ✅ Find existing transaction
        payment = PaymentTransaction.objects.filter(txn_id=razorpay_order_id).first()
        if not payment:
            logger.warning(f"⚠️ Transaction not found | OrderID={razorpay_order_id}")
            return JsonResponse({"ok": False, "error": "Transaction not found"}, status=404)

        # ✅ Attach correct loan reference if missing
        from main.models import LoanRequest, LoanLenderStatus
        if loan_id:
            # Handle both integer ID and loan_id string
            loan = LoanRequest.objects.filter(Q(id=loan_id) | Q(loan_id=loan_id)).first()
            if loan and not payment.loan_request:
                payment.loan_request = loan
                payment.save(update_fields=["loan_request"])
                logger.info(f"🔗 Linked payment {payment.txn_id} → Loan {loan.loan_id}")

        # ✅ Update payment details
        payment.status = "Completed" if verified else "Failed"
        payment.raw_response = dict(data)
        payment.updated_at = timezone.now()
        payment.save(update_fields=["status", "raw_response", "updated_at"])

        # ✅ If verified, sync dashboards (auto approve lender)
        if verified and payment.loan_request:
            loan = payment.loan_request
            lender = payment.user

            # 🔹 Mark loan as Accepted (for applicant dashboard)
            if loan.accepted_lender != lender:
                loan.accepted_lender = lender
                loan.status = "Accepted"
                loan.save(update_fields=["accepted_lender", "status"])
                logger.info(f"📢 Loan {loan.loan_id} marked Accepted by applicant for {lender.email}")

            # 🔹 Update lender feedback (for lender dashboard)
            updated_rows = LoanLenderStatus.objects.filter(
                lender=lender,
                loan=loan
            ).update(
                status="Approved",
                updated_at=timezone.now()
            )

            # ✅ If feedback didn’t exist, create one (failsafe)
            if updated_rows == 0:
                LoanLenderStatus.objects.create(
                    lender=lender,
                    loan=loan,
                    status="Approved"
                )
                logger.info(f"🆕 Created lender feedback entry for {lender.email} → {loan.loan_id}")

        logger.info(f"✅ Payment updated | TxnID={payment.txn_id} | Verified={verified}")

        # ✅ Redirect appropriately
        if verified:
            return redirect(f"/payment/success/?txn_id={razorpay_order_id}")
        else:
            return redirect(f"/payment/failure/?txn_id={razorpay_order_id}")

    except Exception as e:
        logger.error(f"❌ Error during Razorpay callback: {e}", exc_info=True)
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

# ---------------------------------------------------------------------
# ✅ Step 3: Payment Success Page (Auto Invoice + Redirect)
# ---------------------------------------------------------------------
@login_required
def payment_success(request):
    """
    Render payment success summary with auto invoice download 
    and redirect to lender dashboard after success.
    """
    txn_id = request.GET.get("txn_id") or request.GET.get("order_id")
    context = {"status": "unknown", "txn_id": txn_id}

    try:
        if not txn_id:
            context["message"] = "⚠️ Invalid request. No transaction ID provided."
            return render(request, "payments/payment_success.html", context)

        payment = PaymentTransaction.objects.select_related("user").filter(txn_id=txn_id).first()
        if not payment:
            context.update({
                "status": "not_found",
                "message": f"⚠️ No transaction found for ID: {txn_id}",
            })
        else:
            # ✅ Mark payment as completed if pending
            if payment.status not in ["Completed", "Failed"]:
                payment.status = "Completed"
                payment.save(update_fields=["status"])

            user = payment.user
            profile = getattr(user, "profile", None)
            user_name = getattr(profile, "full_name", user.email.split("@")[0])

            context.update({
                "status": "Completed",
                "message": "✅ Payment Successful! Thank you for using Loan Saathi Hub.",
                "amount": payment.amount,
                "date": payment.created_at.strftime("%d %b %Y, %I:%M %p"),
                "payment_method": payment.payment_method,
                "user_email": user.email,
                "user_name": user_name,
                "invoice_number": f"INV-{payment.txn_id[-8:].upper()}",
                "txn_id": payment.txn_id,
            })

    except Exception as e:
        logger.error(f"❌ Error rendering payment_success: {e}", exc_info=True)
        context.update({
            "status": "error",
            "message": "⚠️ Error verifying payment.",
        })

    return render(request, "payments/payment_success.html", context)


# ---------------------------------------------------------------------
# ✅ Step 4: Failure Page
# ---------------------------------------------------------------------
@login_required
@csrf_exempt
def payment_failure(request):
    txn_id = request.GET.get("txn_id")
    context = {"status": "failed", "message": "❌ Payment failed or cancelled."}

    try:
        if txn_id:
            payment = PaymentTransaction.objects.filter(txn_id=txn_id).first()
            if payment and payment.status != "Completed":
                payment.status = "Failed"
                payment.updated_at = timezone.now()
                payment.save(update_fields=["status", "updated_at"])
                logger.warning(f"⚠️ Payment marked Failed | TxnID={txn_id}")
                context["message"] = "❌ Your payment was not successful. Please try again."
            elif not payment:
                context["message"] = f"⚠️ No transaction found for ID: {txn_id}"
        else:
            context["message"] = "⚠️ Transaction ID missing."

    except Exception as e:
        logger.error(f"❌ Error handling payment_failure: {e}", exc_info=True)
        context["message"] = "⚠️ Unexpected error during failure handling."

    return render(request, "payments/payment_failure.html", context)


# ---------------------------------------------------------------------
# ✅ Step 5: Invoice View Page (Download as PDF or View Online)
# ---------------------------------------------------------------------
@login_required
def invoice_view(request):
    txn_id = request.GET.get("txn_id")
    payment = PaymentTransaction.objects.select_related("user").filter(txn_id=txn_id).first()
    if not payment:
        messages.error(request, "Invoice not found.")
        return redirect("dashboard_router")

    total_amount = payment.amount or Decimal("49.00")
    base_amount = (total_amount / Decimal("1.18")).quantize(Decimal("0.01"))
    gst_amount = (total_amount - base_amount).quantize(Decimal("0.01"))

    user = payment.user
    profile = getattr(user, "profile", None)
    user_name = getattr(profile, "full_name", user.email.split("@")[0])

    context = {
        "invoice_number": f"INV-{payment.txn_id[-8:].upper()}",
        "txn_id": payment.txn_id,
        "amount": total_amount,
        "base_amount": base_amount,
        "gst_amount": gst_amount,
        "user_email": user.email,
        "user_name": user_name,
        "date": payment.created_at.strftime("%d %b %Y, %I:%M %p"),
        "payment_method": payment.payment_method or "Razorpay",
    }

    if "download" in request.GET:
        html_content = render_to_string("payments/invoice.html", context)
        pdf = pdfkit.from_string(html_content, False, configuration=pdfkit_config)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{context["invoice_number"]}.pdf"'
        return response

    return render(request, "payments/invoice.html", context)


# -------------------- View Profile (Lender side) --------------------
@login_required
def view_profile(request, loan_id):
    """
    Allows lender to view the applicant's full profile only if:
    1. The lender has completed ₹49 verification payment, AND
    2. The lender is associated with that loan (via LoanLenderStatus or accepted_lender)
    """
    loan = get_object_or_404(LoanRequest, id=loan_id)

    # ✅ Only lenders can access this page
    if getattr(request.user, "role", "").lower() != "lender":
        messages.warning(request, "⚠️ Only lenders can view applicant profiles.")
        return redirect("dashboard_router")

    # ✅ Step 1: Check lender association with this loan
    is_linked = (
        LoanLenderStatus.objects.filter(loan=loan, lender=request.user).exists()
        or loan.accepted_lender == request.user
    )

    if not is_linked:
        messages.error(request, "🚫 You are not associated with this loan request.")
        return redirect("dashboard_lender")

    # ✅ Step 2: Check if lender has completed the ₹49 verification payment
    has_payment = PaymentTransaction.objects.filter(
        user=request.user,
        status__in=["Completed", "Success"]
    ).exists()

    if not has_payment:
        messages.info(request, "💳 Please complete the ₹49 verification payment to unlock full profiles.")
        return redirect("dashboard_lender")

    # ✅ Step 3: Load full applicant details
    applicant = loan.applicant
    profile = getattr(applicant, "profile", None)
    applicant_details = ApplicantDetails.objects.filter(user=applicant).first()

    return render(
        request,
        "view_profile.html",
        {
            "loan": loan,
            "applicant": applicant,
            "profile": profile,
            "applicant_details": applicant_details,
        }
    )


# -------------------- Partial Profile --------------------
@login_required
def partial_profile(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    applicant = loan.applicant
    profile = getattr(applicant, "profile", None)
    applicant_details = ApplicantDetails.objects.filter(user=applicant).first()
    recent_cibil = CibilReport.objects.filter(
        loan=loan, lender=request.user
    ).order_by("-created_at").first()

    hidden_fields = [
        "mobile", "email", "address", "gst_number",
        "company_name", "business_name", "aadhaar_number", "pancard_number",
    ]

    # ✅ Dynamic redirect
    if request.user.is_superuser:
        dashboard_url = reverse("dashboard_admin")
    elif hasattr(request.user, "lender_details"):
        dashboard_url = reverse("dashboard_lender")
    else:
        dashboard_url = reverse("dashboard_applicant")

    return render(
        request,
        "partial_profile.html",
        {
            "loan": loan,
            "applicant": applicant,
            "profile": profile,
            "applicant_details": applicant_details,
            "recent_cibil": recent_cibil,
            "hide_sensitive": True,
            "hidden_fields": hidden_fields,
            "dashboard_url": dashboard_url,
        },
    )
# -------------------- Forgot / Reset Password --------------------
def forgot_password_view(request):
    if request.method=="POST":
        email=(request.POST.get("email") or "").strip().lower()
        try:
            user=User.objects.get(email=email)
            uid=urlsafe_base64_encode(force_bytes(user.pk))
            token=default_token_generator.make_token(user)
            link=request.build_absolute_uri(reverse("reset_password",args=[uid,token]))
            send_mail("🔑 Reset your password",f"Hi {email}, reset here: {link}",settings.DEFAULT_FROM_EMAIL,[email])
            messages.success(request,"✅ Reset email sent.")
        except User.DoesNotExist: messages.error(request,"❌ Email not found.")
    return render(request,"forgot_password.html")

def reset_password_view(request,uidb64,token):
    try: uid=urlsafe_base64_decode(uidb64).decode(); user=User.objects.get(pk=uid)
    except: user=None
    if user and default_token_generator.check_token(user,token):
        form=SetPasswordForm(user,request.POST or None)
        if request.method=="POST" and form.is_valid():
            form.save(); messages.success(request,"✅ Password reset successful."); return redirect("login")
        return render(request,"reset_password.html",{"form":form})
    messages.error(request,"❌ Invalid/expired link."); return redirect("forgot_password")

# -------------------- Support / Complaint / Feedback --------------------
def support_view(request):
    form=SupportForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        ticket=form.save(); send_mail(f"[Support] {ticket.subject}",ticket.message,settings.DEFAULT_FROM_EMAIL,[settings.DEFAULT_FROM_EMAIL])
        return render(request,"support.html",{"form":SupportForm(),"success":True})
    return render(request,"support.html",{"form":form})

def complaint_view(request):
    form=ComplaintForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        c=form.save(); send_mail(f"[Complaint] Against {c.complaint_against or 'Unknown'}",c.message,settings.DEFAULT_FROM_EMAIL,[settings.DEFAULT_FROM_EMAIL])
        return render(request,"complaint.html",{"form":ComplaintForm(),"success":True})
    return render(request,"complaint.html",{"form":form})

def feedback_view(request):
    form=FeedbackForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        fb=form.save(commit=False)
        if request.user.is_authenticated: fb.user=request.user; fb.email=fb.email or request.user.email
        fb.save(); send_mail(f"[Feedback] rating:{fb.rating}",fb.message,settings.DEFAULT_FROM_EMAIL,[settings.DEFAULT_FROM_EMAIL])
        return render(request,"feedback.html",{"form":FeedbackForm(),"success":True})
    return render(request,"feedback.html",{"form":form})

# -------------------- Partial Profile --------------------
@login_required
def partial_profile(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    applicant = loan.applicant
    profile = getattr(applicant, "profile", None)
    applicant_details = ApplicantDetails.objects.filter(user=applicant).first()
    recent_cibil = CibilReport.objects.filter(
        loan=loan, lender=request.user
    ).order_by("-created_at").first()

    hidden_fields = [
        "mobile", "email", "address", "gst_number",
        "company_name", "business_name", "aadhaar_number", "pancard_number",
    ]

    # ✅ Dynamic redirect
    if request.user.is_superuser:
        dashboard_url = reverse("dashboard_admin")
    elif hasattr(request.user, "lender_details"):
        dashboard_url = reverse("dashboard_lender")
    else:
        dashboard_url = reverse("dashboard_applicant")

    return render(
        request,
        "partial_profile.html",
        {
            "loan": loan,
            "applicant": applicant,
            "profile": profile,
            "applicant_details": applicant_details,
            "recent_cibil": recent_cibil,
            "hide_sensitive": True,
            "hidden_fields": hidden_fields,
            "dashboard_url": dashboard_url,
        },
    )


# -------------------- Manual CIBIL for Profile --------------------
@login_required
def generate_cibil_score_manual(request):
    """
    Allow applicants to manually enter or update their CIBIL score
    from the Profile Form or Edit Profile page.
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "msg": "Invalid request method."}, status=405)

    score = request.POST.get("cibil_score")
    if not score:
        return JsonResponse({"ok": False, "msg": "Please enter your CIBIL score."}, status=400)

    try:
        score = int(score)
        if score < 350 or score > 950:
            return JsonResponse({"ok": False, "msg": "CIBIL score must be between 350 and 950."}, status=400)
    except ValueError:
        return JsonResponse({"ok": False, "msg": "Invalid input. Please enter a numeric value."}, status=400)

    # ✅ Get or create ApplicantDetails record
    details, _ = ApplicantDetails.objects.get_or_create(user=request.user)

    # ✅ Update with timestamp
    details.cibil_score = score
    details.cibil_last_generated = timezone.now()
    details.cibil_generated_by = None  # manual input → no lender
    details.save(update_fields=["cibil_score", "cibil_last_generated", "cibil_generated_by"])

    # ✅ Set success message for redirect pages
    messages.success(request, f"✅ CIBIL score {score} updated successfully!")

    # ✅ Return appropriate response for AJAX / normal requests
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": True,
            "score": score,
            "msg": f"CIBIL score {score} updated successfully.",
            "redirect_url": reverse("edit_profile", args=[request.user.id])
        })

    return redirect("edit_profile", user_id=request.user.id)




# -------------------- OTP Resend --------------------
def resend_email_otp_view(request):
    email=request.session.get("reg_email")
    if not email: return JsonResponse({"ok":False,"msg":"Session expired"})
    otp_data=send_email_otp(email)
    if otp_data.get("ok"):
        request.session["otp"]=otp_data["otp"]; request.session["otp_expiry"]=(now()+timedelta(minutes=5)).isoformat()
        return JsonResponse({"ok":True,"msg":"New OTP sent"})
    return JsonResponse({"ok":False,"msg":"Failed to resend OTP"})


# --------------- Gmail View in Admin Dashboard ---------------

def fetch_emails(folder="inbox", search="ALL", limit=15):
    """Fetch emails safely from Gmail IMAP and return structured list."""
    mails = []
    try:
        # ✅ Connect securely to Gmail IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

        # ✅ Select folder (case-insensitive)
        mail.select(folder)

        # ✅ Search emails
        status, data = mail.search(None, search)
        if status != "OK" or not data or not data[0]:
            return [{"from": "System", "subject": "No emails found", "date": "", "snippet": ""}]

        # ✅ Process latest messages
        for num in data[0].split()[-limit:]:
            _, raw = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(raw[0][1])

            snippet = ""
            payload = msg.get_payload()

            # ✅ Handle multipart messages
            if isinstance(payload, list):
                for part in payload:
                    ctype = part.get_content_type()
                    if ctype == "text/plain":
                        snippet = part.get_payload(decode=True).decode(errors="ignore")[:200]
                        break
                    elif ctype == "text/html" and not snippet:
                        snippet = part.get_payload(decode=True).decode(errors="ignore")[:200]
            else:
                if isinstance(payload, bytes):
                    snippet = payload.decode(errors="ignore")[:200]
                elif isinstance(payload, str):
                    snippet = payload[:200]

            mails.append({
                "from": msg.get("From"),
                "to": msg.get("To"),
                "subject": msg.get("Subject") or "(No Subject)",
                "date": msg.get("Date"),
                "snippet": snippet.strip() if snippet else "(No content)",
            })

        mail.logout()

    except imaplib.IMAP4.error as e:
        mails = [{"from": "Error", "subject": f"IMAP login failed: {e}", "date": "", "snippet": ""}]
    except Exception as e:
        mails = [{"from": "Error", "subject": str(e), "date": "", "snippet": ""}]
    return mails

# ------------------------- Admin Emails (Gmail Integration) -------------------------
@login_required
def admin_emails(request):
    """
    Display Gmail Inbox and Sent emails for admin users,
    along with categorized filters like OTP, Complaints, Feedback, etc.
    """
    if not request.user.is_superuser:
        return redirect("dashboard_admin")

    try:
        # ✅ Fetch latest 20 emails from Inbox and Sent
        inbox = fetch_emails("inbox", limit=20)
        sent = fetch_emails('"[Gmail]/Sent Mail"', limit=20)

        # ✅ Apply subject-based categorization (case-insensitive)
        otp = [m for m in inbox if m.get("subject") and "otp" in m["subject"].lower()]
        complaints = [m for m in inbox if m.get("subject") and "complaint" in m["subject"].lower()]
        feedback = [m for m in inbox if m.get("subject") and "feedback" in m["subject"].lower()]
        deleted_users = [m for m in inbox if m.get("subject") and "deleted" in m["subject"].lower()]

        # ✅ Sort emails by date (latest first when possible)
        def parse_date_safe(mail_item):
            from email.utils import parsedate_to_datetime
            try:
                return parsedate_to_datetime(mail_item.get("date"))
            except Exception:
                return None

        inbox.sort(key=parse_date_safe, reverse=True)
        sent.sort(key=parse_date_safe, reverse=True)

        context = {
            "inbox": inbox,
            "sent": sent,
            "otp": otp,
            "complaints": complaints,
            "feedback": feedback,
            "deleted_users": deleted_users,
        }

    except Exception as e:
        # ✅ Catch any unexpected Gmail/IMAP error
        context = {
            "inbox": [{"from": "Error", "subject": f"Gmail Error: {e}", "date": "", "snippet": ""}],
            "sent": [],
            "otp": [],
            "complaints": [],
            "feedback": [],
            "deleted_users": [],
        }

    return render(request, "admin_emails.html", context)


# --------------- Gmail Compose ---------------
@login_required
def admin_email_compose(request):
    if not request.user.is_superuser:
        return redirect("dashboard_admin")

    if request.method == "POST":
        to = request.POST.get("to")
        subject = request.POST.get("subject")
        body = request.POST.get("body")

        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = settings.EMAIL_HOST_USER
            msg["To"] = to

            smtp = smtplib.SMTP("smtp.gmail.com", 587)
            smtp.starttls()
            smtp.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            smtp.sendmail(settings.EMAIL_HOST_USER, [to], msg.as_string())
            smtp.quit()
            return redirect("admin_emails")
        except Exception as e:
            return render(request, "admin_email_compose.html", {"error": str(e)})

    return render(request, "admin_email_compose.html")

# ---------------------------------------------------------------------
# ✅ Expense & Profit Projection Dashboard (with Chart)
# ---------------------------------------------------------------------

@login_required
def pricing_projection(request):
    """
    Displays monthly cost, revenue, and profit estimation based on
    number of loans processed per month (₹49 per loan model).
    Includes Chart.js visualization.
    """
    # --- Configurable constants ---
    per_loan_fee = Decimal("49.00")  # ₹49 per loan
    razorpay_fee_percent = Decimal("2.36")  # Razorpay % fee
    razorpay_flat_fee = Decimal("3.00")  # per transaction ₹3 fixed
    fixed_server_cost = Decimal("10000.00")
    marketing_cost = Decimal("12000.00")
    maintenance_cost = Decimal("8000.00")
    misc_cost = Decimal("2000.00")

    # --- Input ---
    loan_count = int(request.GET.get("loans", 1000))

    # --- Base calculations ---
    gross_revenue = per_loan_fee * loan_count
    gateway_fees = ((gross_revenue * razorpay_fee_percent) / 100) + (razorpay_flat_fee * loan_count)
    total_fixed_costs = fixed_server_cost + marketing_cost + maintenance_cost + misc_cost
    total_expense = total_fixed_costs + gateway_fees
    net_profit = gross_revenue - total_expense

    # --- Break-even analysis ---
    try:
        per_loan_net = per_loan_fee - (per_loan_fee * razorpay_fee_percent / 100) - razorpay_flat_fee
        break_even_loans = math.ceil(float(total_fixed_costs / per_loan_net)) if per_loan_net > 0 else 0
    except Exception:
        break_even_loans = 0

    avg_cost_per_loan = (total_expense / loan_count) if loan_count else 0

    # --- Generate chart data dynamically ---
    loan_range = list(range(100, 2100, 100))  # 100 to 2000 loans
    profit_data = []
    for n in loan_range:
        revenue = per_loan_fee * n
        fees = ((revenue * razorpay_fee_percent) / 100) + (razorpay_flat_fee * n)
        total_cost = total_fixed_costs + fees
        profit = revenue - total_cost
        profit_data.append(round(profit, 2))

    ctx = {
        "loan_count": loan_count,
        "gross_revenue": gross_revenue,
        "gateway_fees": gateway_fees,
        "total_fixed_costs": total_fixed_costs,
        "total_expense": total_expense,
        "net_profit": net_profit,
        "avg_cost_per_loan": avg_cost_per_loan,
        "break_even_loans": break_even_loans,
        "per_loan_fee": per_loan_fee,
        "loan_range": loan_range,
        "profit_data": profit_data,
    }
    return render(request, "admin/pricing_projection.html", ctx)


# ----------------Offline fallback message-------------------
def offline_page(request):
    """Simple offline fallback page."""
    return render(request, "offline.html")

# ----------------Rate Limit-------------------
from django_ratelimit.decorators import ratelimit
from django.shortcuts import render
from django.http import HttpResponseForbidden

@ratelimit(key='ip', rate='5/m', block=True)
def login_view(request):
    # This allows only 5 attempts per minute per IP
    # The rest of your login logic here
    if request.method == 'POST':
        # authenticate logic
        ...
    return render(request, 'login.html')

# ----------------Advertisement (page view index-------------------
def advertise_view(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        ad_position = request.POST.get("position", "")
        ad_size = request.POST.get("size", "")
        message = request.POST.get("message", "")

        if not all([name, email, ad_position, ad_size]):
            return JsonResponse({"ok": False, "msg": "All required fields must be filled."})

        subject = f"📰 New Advertisement Request from {name}"
        content = f"""
New advertisement request received:

👤 Name: {name}
📧 Email: {email}
📞 Phone: {phone or 'N/A'}

📍 Position: {ad_position}
📏 Size: {ad_size}

💬 Message:
{message or 'No message provided.'}
"""

        try:
            send_mail(
                subject,
                content,
                settings.DEFAULT_FROM_EMAIL,
                ["loansaathihub@gmail.com"],
                fail_silently=False,
            )
            logger.info(f"✅ Ad request email sent from {email}")
            return JsonResponse({"ok": True, "msg": "Your advertisement request has been sent!"})
        except Exception as e:
            logger.exception("❌ Failed to send advertisement email")
            return JsonResponse({"ok": False, "msg": f"Error sending email: {e}"})

    return render(request, "advertise.html")


# =====================================================
# 🔹 HEALTHCHECK ENDPOINT (For Render / Monitoring)
# =====================================================
def healthcheck_view(request):
    """
    ✅ Simple health check for Render and uptime monitors.
    Returns 200 OK if DB + cache (optional) + Django settings are valid.
    """
    try:
        # 🧠 Check database connection (if active)
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            db_ok = True
    except Exception as e:
        db_ok = False

    return JsonResponse({
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "debug": settings.DEBUG,
        "environment": "Render" if not settings.DEBUG else "Local",
    })


