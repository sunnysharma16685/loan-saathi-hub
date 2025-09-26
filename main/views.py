import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import (
    authenticate, login, logout, get_user_model
)
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm
from django.http import JsonResponse
from django.urls import reverse
from django.conf import settings
from django.utils.dateparse import parse_date
from django.db.models import Q
import uuid, random
from django.db import migrations, models
from datetime import date
import re, uuid, random
from django.views.decorators.http import require_http_methods
from django.db import transaction


logger = logging.getLogger(__name__)

# -------------------- Local Models --------------------
from .models import (
    User,
    Profile,
    ApplicantDetails,
    LenderDetails,
    LoanRequest,
    LoanLenderStatus,
    Payment,
    SupportTicket,
    Complaint,
    Feedback,
    CibilReport,
)

# -------------------- Local Forms --------------------
from .forms import (
    ApplicantRegistrationForm,
    LenderRegistrationForm,
    LoginForm,
    SupportForm,
    ComplaintForm,
    FeedbackForm,
)

# Ensure User refers to the active custom user model
User = get_user_model()


# -------------------- Home --------------------
def index(request):
    return render(request, 'index.html')


# -------------------- Helper: Profile Check --------------------
def is_profile_complete(user):
    profile = getattr(user, "profile", None) or Profile.objects.filter(user=user).first()
    if not profile or not profile.full_name or not profile.pancard_number or not getattr(profile, "mobile", None):
        return False

    if getattr(user, "role", None) == "applicant":
        details = getattr(user, "applicantdetails", None) or ApplicantDetails.objects.filter(user=user).first()
        return bool(details and (details.employment_type or details.company_name or details.business_name))

    if getattr(user, "role", None) == "lender":
        details = getattr(user, "lenderdetails", None) or LenderDetails.objects.filter(user=user).first()
        return bool(details and (details.lender_type or details.bank_firm_name))

    return True

# -------------------- Register --------------------
def register_view(request):
    role = (request.GET.get("role") or "").lower()

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        confirm_password = request.POST.get("confirm_password") or ""
        form_role = (request.POST.get("role") or role).lower()

        if form_role not in ("applicant", "lender"):
            messages.error(request, "Please select applicant or lender.")
            return redirect(f"/register/?role={role or ''}")

        if not email or not password:
            messages.error(request, "Email and password are required.")
            return redirect(f"/register/?role={form_role}")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect(f"/register/?role={form_role}")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect(f"/register/?role={form_role}")

        try:
            # ✅ Create user
            user = User(email=email, role=form_role)
            user.set_password(password)
            user.save()

            # ❌ Profile auto-create मत करो (PAN/Aadhaar missing होंगे तो error आएगा)
            # ✅ सिर्फ़ auto-login करा दो
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            # ✅ Redirect to profile form (user यहाँ अपना PAN/Aadhaar fill करेगा)
            return redirect("profile_form", user_id=str(user.id))

        except Exception as e:
            messages.error(request, f"Registration error: {e}")
            return redirect(f"/register/?role={form_role}")

    return render(request, "register.html", {"role": role})


# -------------------- Login --------------------
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import redirect, render
import logging

logger = logging.getLogger(__name__)

def login_view(request):
    role = (request.GET.get("role") or "").lower()

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        form_role = (request.POST.get("role") or role).lower()

        # ✅ Try authentication with email or username fallback
        user = authenticate(request, email=email, password=password) or \
               authenticate(request, username=email, password=password)

        if user:
            # ✅ Role check
            if form_role and getattr(user, "role", None) != form_role:
                messages.error(request, "❌ Role mismatch. Please select the correct role.")
                return redirect(f"/login/?role={form_role}")

            profile = getattr(user, "profile", None)

            # ✅ If profile missing
            if not profile:
                messages.error(request, "⚠️ Profile not found. Please contact support.")
                return redirect("login")

            # ✅ Handle profile statuses
            if profile.status == "Hold":
                # Keep user logged in so review_profile works
                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                messages.warning(request, "⚠️ Your profile is pending admin approval.")
                return redirect("review_profile")

            if profile.status == "Deactivated":
                messages.error(
                    request,
                    "🚫 Your profile has been deactivated. "
                    "Please check your registered email for the reason."
                )
                return redirect("login")

            if profile.status == "Deleted":
                messages.error(request, "❌ This account has been permanently deleted.")
                return redirect("login")

            if profile.status != "Active":
                logger.error("Unknown profile.status for user %s: %s", getattr(user, "id", None), profile.status)
                messages.error(request, "⚠️ Your profile is not active. Please contact support.")
                return redirect("login")

            # ✅ Success login
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            # If profile incomplete → go to profile_form
            if not is_profile_complete(user):
                messages.info(request, "ℹ️ Please complete your profile first.")
                return redirect("profile_form", user_id=str(user.id))

            # Else → send to dashboard
            messages.success(request, f"✅ Welcome back, {profile.full_name or user.email}!")
            return redirect("dashboard_router")

        else:
            messages.error(request, "❌ Invalid email or password.")

    return render(request, "login.html", {"role": role})

# -------------------- Logout --------------------
def logout_view(request):
    logout(request)
    messages.success(request, "✅ Logged out successfully")
    return redirect("/")


# -------------------- Profile Form --------------------

@login_required
def profile_form(request, user_id):
    logger.error("🔎 Entered profile_form for user_id=%s by %s", user_id, request.user.email)

    user = get_object_or_404(User, id=user_id)

    # ✅ Prevent unauthorized edit
    if request.user.id != user.id and not request.user.is_superuser:
        messages.error(request, "You are not allowed to edit this profile.")
        return redirect("index")

    role = (user.role or "").lower()

    # ✅ Ensure profile exists with dummy KYC defaults if created
    profile, created = Profile.objects.get_or_create(
        user=user,
        defaults={
            "full_name": user.email.split("@")[0],
            "status": "Hold",
            "pancard_number": f"DUMMY{uuid.uuid4().hex[:4].upper()}X",
            "aadhaar_number": str(random.randint(10**11, 10**12 - 1)),
        },
    )

    applicant_details = ApplicantDetails.objects.filter(user=user).first() if role == "applicant" else None
    lender_details = LenderDetails.objects.filter(user=user).first() if role == "lender" else None

    # Helper to safely extract POST values
    def G(*keys):
        for k in keys:
            v = request.POST.get(k)
            if v and str(v).strip():
                return str(v).strip()
        return None

    if request.method == "POST":
        logger.error("📥 Profile POST data = %s", request.POST.dict())

        errors = {}

        # ✅ PAN validation
        pancard_number = G("pancard_number", "panCardNumber")
        if not pancard_number:
            errors["pancard_number"] = "PAN Card Number is required."
        elif not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pancard_number.upper()):
            errors["pancard_number"] = "Invalid PAN format. Example: ABCDE1234F"
        elif Profile.objects.filter(pancard_number=pancard_number.upper()).exclude(user=user).exists():
            errors["pancard_number"] = f"PAN {pancard_number} already exists."

        # ✅ Aadhaar validation
        aadhaar_number = G("aadhaar_number", "aadhaarNumber")
        if not aadhaar_number:
            errors["aadhaar_number"] = "Aadhaar Number is required."
        elif not re.match(r"^\d{12}$", aadhaar_number):
            errors["aadhaar_number"] = "Invalid Aadhaar format. Example: 123456789012"
        elif Profile.objects.filter(aadhaar_number=aadhaar_number).exclude(user=user).exists():
            errors["aadhaar_number"] = f"Aadhaar {aadhaar_number} already exists."

        if errors:
            for field, msg in errors.items():
                messages.error(request, msg)
            return render(request, "profile_form.html", {
                "user": user,
                "profile": profile,
                "role": role.capitalize() if role else "",
                "applicant_details": applicant_details,
                "lender_details": lender_details,
                "errors": errors,
            })

        # ✅ Save profile fields
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
        profile.aadhaar_number = aadhaar_number
        profile.save()

        logger.error("✅ Profile saved for %s", user.email)

        # ✅ Applicant / Lender details
        if role == "applicant":
            details, _ = ApplicantDetails.objects.get_or_create(user=user)
            details.employment_type = G("employment_type", "employmentType") or details.employment_type
            cibil_val = G("cibil_score")
            details.cibil_score = int(cibil_val) if cibil_val and cibil_val.isdigit() else details.cibil_score
            details.save()
            applicant_details = details

        elif role == "lender":
            l, _ = LenderDetails.objects.get_or_create(user=user)
            l.lender_type = G("lender_type") or l.lender_type
            l.bank_firm_name = G("bank_firm_name", "bankfirmName") or l.bank_firm_name
            l.branch_name = G("branch_name", "branchName") or l.branch_name
            l.dsa_code = G("dsa_code", "dsaCode") or l.dsa_code
            l.designation = G("designation") or l.designation
            l.gst_number = G("gst_number", "gstNumber") or l.gst_number
            l.save()
            lender_details = l

        messages.success(request, "✅ Profile saved successfully.")
        return redirect("review_profile")

    return render(request, "profile_form.html", {
        "user": user,
        "profile": profile,
        "role": role.capitalize() if role else "",
        "applicant_details": applicant_details,
        "lender_details": lender_details,
    })


# -------------------- Edit Profile --------------------
@login_required
def edit_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.user.id != user.id and not request.user.is_superuser:
        messages.error(request, "You are not allowed to edit this profile.")
        return redirect("index")

    profile, _ = Profile.objects.get_or_create(user=user)
    applicant_details = None
    lender_details = None

    if user.role == "applicant":
        applicant_details, _ = ApplicantDetails.objects.get_or_create(user=user)
    elif user.role == "lender":
        lender_details, _ = LenderDetails.objects.get_or_create(user=user)

    if request.method == "POST":
        # 🔒 Locked fields (always from DB, not from form)
        profile.full_name = profile.full_name or request.POST.get("full_name")
        profile.dob = profile.dob
        profile.mobile = profile.mobile
        profile.pancard_number = profile.pancard_number
        profile.aadhaar_number = profile.aadhaar_number

        # Editable fields
        profile.gender = request.POST.get("gender")
        profile.marital_status = request.POST.get("marital_status")
        profile.address = request.POST.get("address")
        profile.pincode = request.POST.get("pincode")
        profile.city = request.POST.get("city")
        profile.state = request.POST.get("state")

        profile.save()

        # Applicant details
        if user.role == "applicant":
            applicant_details.employment_type = request.POST.get("employment_type")
            applicant_details.company_name = request.POST.get("company_name")
            applicant_details.company_type = request.POST.get("company_type")
            applicant_details.designation = request.POST.get("designation")
            applicant_details.itr = request.POST.get("itr")
            applicant_details.current_salary = request.POST.get("current_salary") or None
            applicant_details.other_income = request.POST.get("other_income") or None
            applicant_details.total_emi = request.POST.get("total_emi") or None

            # Business fields
            applicant_details.business_name = request.POST.get("business_name")
            applicant_details.business_type = request.POST.get("business_type")
            applicant_details.business_sector = request.POST.get("business_sector")
            applicant_details.total_turnover = request.POST.get("total_turnover") or None
            applicant_details.last_year_turnover = request.POST.get("last_year_turnover") or None
            applicant_details.business_total_emi = request.POST.get("business_total_emi") or None
            applicant_details.business_itr_status = request.POST.get("business_itr_status")

            applicant_details.save()
            messages.success(request, "✅ Applicant profile updated successfully!")
            return redirect("edit_profile", user_id=user.id)  # same page reload

        # Lender details
        elif user.role == "lender":
            lender_details.lender_type = request.POST.get("lender_type")
            lender_details.dsa_code = request.POST.get("dsa_code")
            lender_details.bank_firm_name = request.POST.get("bank_firm_name")
            lender_details.gst_number = request.POST.get("gst_number")
            lender_details.branch_name = request.POST.get("branch_name")
            lender_details.designation = request.POST.get("designation")
            lender_details.save()
            messages.success(request, "✅ Lender profile updated successfully!")
            return redirect("edit_profile", user_id=user.id)  # same page reload

    return render(
        request,
        "edit_profile.html",
        {
            "user": user,
            "profile": profile,
            "role": user.role.capitalize(),
            "applicant_details": applicant_details,
            "lender_details": lender_details,
            "dashboard_url": reverse("dashboard_applicant") if user.role == "applicant" else reverse("dashboard_lender"),
        },
    )



# -------------------- Admin Login --------------------
def admin_login(request):
    if request.method == "POST":
        identifier = (request.POST.get("identifier") or "").strip()
        password = (request.POST.get("password") or "").strip()

        user = None
        if identifier:
            # 🔎 check by email OR mobile
            user = (
                User.objects.filter(email__iexact=identifier).first()
                or User.objects.filter(profile__mobile=identifier).first()
            )

        if user:
            # ✅ use email because USERNAME_FIELD = "email"
            auth_user = authenticate(request, email=user.email, password=password)

            if auth_user and auth_user.is_superuser:
                login(request, auth_user)
                return redirect("dashboard_admin")  # redirect on success
            else:
                messages.error(request, "❌ Invalid password or not an admin user.")
        else:
            messages.error(request, "❌ User not found.")

    return render(request, "admin_login.html")

# -------------------- Admin: Full Profile (Applicant & Lender)--------------------
@login_required
def admin_view_profile(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, "Admins only.")
        return redirect("dashboard_admin")

    user = get_object_or_404(User, id=user_id)
    profile = getattr(user, "profile", None)
    applicant_details = ApplicantDetails.objects.filter(user=user).first() if user.role == "applicant" else None
    lender_details = LenderDetails.objects.filter(user=user).first() if user.role == "lender" else None

    return render(request, "admin_full_profile.html", {
        "user": user, "profile": profile,
        "applicant_details": applicant_details,
        "lender_details": lender_details,
    })


# -------------------- Review Profile (Applicant & Lender)--------------------
@login_required
def review_profile(request):
    return render(request, "review_profile.html")


# -------------------- Redirect After Login Review Page--------------------
def redirect_after_login(user):
    if not hasattr(user, "profile"):
        return "profile_form"

    if user.profile.status != "Active":
        return "review_profile"

    if user.role == "applicant":
        return "dashboard_applicant"
    elif user.role == "lender":
        return "dashboard_lender"
    return "index"



# -------------------- Admin Dashboard --------------------
@login_required
def dashboard_admin(request):
    if not request.user.is_superuser:
        messages.error(request, "Admins only.")
        return redirect("index")

    users_qs = User.objects.all().order_by("-created_at")
    applicants = ApplicantDetails.objects.select_related("user").all().order_by("-id")
    lenders = LenderDetails.objects.select_related("user").all().order_by("-id")
    loans = LoanRequest.objects.select_related("applicant", "accepted_lender").all().order_by("-created_at")
    payments = Payment.objects.select_related("lender", "loan_request").all().order_by("-id")

    return render(request, "dashboard_admin.html", {
        "users": users_qs, "applicants": applicants, "lenders": lenders,
        "loans": loans, "payments": payments,
    })


# -------------------- Admin: User Actions --------------------
@login_required
@require_http_methods(["GET", "POST", "HEAD"])
@csrf_protect
def admin_user_action(request, user_id):
    """
    POST -> perform admin actions (accept / deactivate / activate / delete)
    GET/HEAD -> friendly redirect to dashboard (prevents 405 HEAD/GET spam in logs)
    """
    # Only superusers may proceed
    if not request.user.is_superuser:
        messages.error(request, "🚫 Access denied.")
        return redirect("dashboard_admin")

    # Handle safe GET / HEAD: no action, just redirect back
    if request.method in ("GET", "HEAD"):
        return redirect("dashboard_admin")

    # At this point it's POST
    action = (request.POST.get("action") or "").lower()
    reason = (request.POST.get("reason") or "").strip()[:1000]

    try:
        # ✅ Optimized: load profile in one query
        target = User.objects.select_related("profile").get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "❌ User not found.")
        return redirect("dashboard_admin")

    profile = getattr(target, "profile", None)
    support_from = getattr(settings, "DEFAULT_FROM_EMAIL", "loansaathihub@gmail.com")
    orig_email = target.email
    full_name = getattr(profile, "full_name", orig_email)

    try:
        # Use a DB transaction to keep updates atomic
        with transaction.atomic():
            if action == "accept":
                if profile:
                    profile.status = "Active"
                    profile.is_reviewed = True
                    profile.is_blocked = False
                    profile.save(update_fields=["status", "is_reviewed", "is_blocked"])
                target.is_active = True
                target.save(update_fields=["is_active"])

                try:
                    send_mail(
                        "✅ Profile Approved — Loan Saathi Hub",
                        f"Dear {full_name},\n\nYour profile has been approved successfully. You can now login.\n\nRegards,\nLoan Saathi Hub",
                        support_from,
                        [orig_email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.exception("Error sending approval email for user %s: %s", user_id, e)

                messages.success(request, "✅ User profile approved successfully.")

            elif action == "deactivate":
                target.is_active = False
                target.save(update_fields=["is_active"])
                if profile:
                    profile.status = "Deactivated"
                    profile.is_blocked = True
                    profile.save(update_fields=["status", "is_blocked"])

                try:
                    send_mail(
                        "⚠️ Account Deactivated — Loan Saathi Hub",
                        f"Dear {full_name},\n\nYour account has been deactivated.\nReason: {reason or 'Policy violation'}\n\nRegards,\nLoan Saathi Hub",
                        support_from,
                        [orig_email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.exception("Error sending deactivation email for user %s: %s", user_id, e)

                messages.warning(request, "⚠️ User profile deactivated.")

            elif action == "activate":
                target.is_active = True
                target.save(update_fields=["is_active"])
                if profile:
                    profile.status = "Active"
                    profile.is_blocked = False
                    profile.save(update_fields=["status", "is_blocked"])

                try:
                    send_mail(
                        "✅ Account Reactivated — Loan Saathi Hub",
                        f"Dear {full_name},\n\nGood news! Your account has been re-activated.\n\nRegards,\nLoan Saathi Hub",
                        support_from,
                        [orig_email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.exception("Error sending reactivate email for user %s: %s", user_id, e)

                messages.success(request, "✅ User profile re-activated.")

            elif action == "delete":
                target.is_active = False
                target.email = f"disabled+{target.id}@blocked.loansaathihub"
                if hasattr(target, "username"):
                    target.username = f"disabled_{target.id}"
                    target.save(update_fields=["is_active", "email", "username"])
                else:
                    target.save(update_fields=["is_active", "email"])

                if profile:
                    profile.status = "Deleted"
                    profile.is_blocked = True
                    profile.save(update_fields=["status", "is_blocked"])

                try:
                    send_mail(
                        "🗑️ Account Deleted — Loan Saathi Hub",
                        f"Dear {full_name},\n\nYour account has been permanently deleted from Loan Saathi Hub.\n\nRegards,\nLoan Saathi Hub",
                        support_from,
                        [orig_email],
                        fail_silently=True,
                    )
                except Exception as e:
                    logger.exception("Error sending delete email for user %s: %s", user_id, e)

                messages.success(request, "🗑️ User profile deleted permanently.")

            else:
                messages.error(request, "❌ Unknown action requested.")

    except Exception as e:
        logger.exception("Error processing admin_user_action for user %s, action=%s: %s", user_id, action, e)
        messages.error(request, f"⚠️ Error processing action: {e}")

    return redirect("dashboard_admin")

# -------------------- Dashboard Logout---------------

@login_required
def admin_logout(request):
    logout(request)
    messages.success(request, "✅ Admin logged out successfully")
    return redirect("admin_login")

# -------------------- Dashboard Router --------------------
@login_required
def dashboard_router(request):
    if request.user.is_superuser:
        return redirect("dashboard_admin")

    role = getattr(request.user, "role", None)
    profile = getattr(request.user, "profile", None)

    # 🚨 If profile under review → redirect to review page
    if profile and not profile.is_reviewed:
        return render(request, "review_profile.html", {"profile": profile})

    if role == "lender":
        return redirect("dashboard_lender")
    elif role == "applicant":
        return redirect("dashboard_applicant")

    return redirect("index")


# -------------------- Applicant Dashboard --------------------
@login_required
def dashboard_applicant(request):
    profile = getattr(request.user, "profile", None)
    if profile and not profile.is_reviewed:
        # 🚨 Block until admin approves
        return render(request, "review_profile.html", {"profile": profile})

    loans = LoanRequest.objects.filter(applicant=request.user).prefetch_related("lender_statuses").order_by("-created_at")
    today = date.today()

    for loan in loans:
        statuses = loan.lender_statuses.all() if hasattr(loan, "lender_statuses") else []
        if loan.status == "Accepted":
            loan.global_status, loan.global_remarks = "Approved", "✅ You accepted this lender."
        elif loan.status == "Finalised":
            loan.global_status, loan.global_remarks = "Rejected", "❌ You finalised another lender."
        elif not statuses or all(ls.status == "Pending" for ls in statuses):
            loan.global_status, loan.global_remarks = "Pending", "⌛ Lender reviewing your loan."
        elif any(ls.status == "Approved" for ls in statuses):
            loan.global_status, loan.global_remarks = "Approved", "✅ A lender approved your loan."
        elif all(ls.status == "Rejected" for ls in statuses):
            loan.global_status, loan.global_remarks = "Rejected", "❌ All lenders rejected this loan."
        else:
            loan.global_status, loan.global_remarks = "Pending", "⌛ Lender reviewing your loan."

    context = {
        "loans": loans,
        "total_today": loans.filter(created_at__date=today).count(),
        "total_approved": loans.filter(status="Accepted").count(),
        "total_rejected": loans.filter(status="Finalised").count(),
        "total_pending": loans.filter(status="Pending").count(),
    }
    return render(request, "dashboard_applicant.html", context)


# -------------------- Lender Dashboard --------------------
@login_required
def dashboard_lender(request):
    profile = getattr(request.user, "profile", None)
    if profile and not profile.is_reviewed:
        # 🚨 Block until admin approves
        return render(request, "review_profile.html", {"profile": profile})

    lender_feedbacks = LoanLenderStatus.objects.filter(lender=request.user).select_related("loan", "loan__applicant").order_by("-updated_at")

    for fb in lender_feedbacks:
        loan = fb.loan
        if loan.status == "Accepted" and loan.accepted_lender == request.user:
            fb.loan.global_status = "Approved"
        elif loan.status in ["Accepted", "Finalised"] and loan.accepted_lender != request.user:
            fb.loan.global_status = "Rejected"
        else:
            fb.loan.global_status = fb.status

    today = timezone.now().date()
    total_today = lender_feedbacks.filter(loan__created_at__date=today).count()
    total_approved = sum(1 for fb in lender_feedbacks if fb.loan.global_status == "Approved")
    total_rejected = sum(1 for fb in lender_feedbacks if fb.loan.global_status == "Rejected")
    total_pending = sum(1 for fb in lender_feedbacks if fb.loan.global_status == "Pending")

    handled_loans = LoanLenderStatus.objects.filter(lender=request.user).values_list("loan_id", flat=True)
    pending_loans = LoanRequest.objects.filter(status="Pending", accepted_lender__isnull=True).exclude(id__in=handled_loans).select_related("applicant").order_by("-created_at")
    finalised_loans = LoanRequest.objects.filter(status__in=["Accepted", "Finalised"]).select_related("applicant", "accepted_lender")

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
def applicant_accept_loan(request, loan_id, lender_id):
    loan = get_object_or_404(LoanRequest, id=loan_id, applicant=request.user)
    lender = get_object_or_404(User, id=lender_id, role="lender")
    loan.status, loan.accepted_lender = "Accepted", lender
    loan.save()
    messages.success(request, "✅ You accepted this lender.")
    return redirect("dashboard_applicant")


# -------------------- Loan Request --------------------
@login_required
def loan_request(request):
    if request.method == "POST" and request.user.role == "applicant":
        loan_id = "LSH" + get_random_string(6, allowed_chars="0123456789")
        loan = LoanRequest.objects.create(
            id=uuid.uuid4(), loan_id=loan_id, applicant=request.user,
            loan_type=request.POST.get("loan_type") or "",
            amount_requested=request.POST.get("amount_requested") or 0,
            duration_months=request.POST.get("duration_months") or 0,
            interest_rate=request.POST.get("interest_rate") or 0,
            reason_for_loan=request.POST.get("reason_for_loan") or "", status="Pending")
        for lender in User.objects.filter(role="lender"):
            LoanLenderStatus.objects.create(loan=loan, lender=lender, status="Pending", remarks="Lender Reviewing")
        messages.success(request, f"✅ Loan {loan.loan_id} submitted.")
        return redirect("dashboard_router")
    return render(request, "loan_request.html")


# -------------------- Approve / Reject --------------------
@login_required
def reject_loan(request, loan_id):
    if request.method == "POST":
        reason = request.POST.get("reason")
        loan = get_object_or_404(LoanRequest, id=loan_id)
        lender_status = get_object_or_404(LoanLenderStatus, loan=loan, lender=request.user)
        lender_status.status, lender_status.remarks = "Rejected", reason
        lender_status.save()
        messages.warning(request, f"Loan {loan.loan_id} rejected: {reason}")
        return redirect("dashboard_lender")


@login_required
def approve_loan(request, loan_id):
    ls = get_object_or_404(LoanLenderStatus, loan__id=loan_id, lender=request.user)
    ls.status, ls.remarks = "Approved", "Payment done, Loan Approved"
    ls.save()
    messages.success(request, f"Loan {ls.loan.loan_id} approved.")
    return redirect("dashboard_lender")


# -------------------- Payments --------------------
@login_required
def payment_page(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    if request.method == "POST":
        Payment.objects.create(lender=request.user, loan_request=loan,
            payment_method=request.POST.get("payment_method"),
            amount=request.POST.get("amount"), status="Completed")
        ls = get_object_or_404(LoanLenderStatus, loan=loan, lender=request.user)
        ls.status, ls.remarks = "Approved", "Payment done, Loan Approved"
        ls.save()
        messages.success(request, f"✅ Loan {loan.loan_id} approved after payment.")
        return redirect("dashboard_lender")
    return render(request, "payment.html", {"loan": loan})


@login_required
def make_dummy_payment(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    Payment.objects.create(loan_request=loan, lender=request.user,
        amount=loan.amount_requested, status="Completed", payment_method="Dummy")
    ls = get_object_or_404(LoanLenderStatus, loan=loan, lender=request.user)
    ls.status, ls.remarks = "Approved", "Dummy Payment done"
    ls.save()
    messages.success(request, f"✅ Dummy Payment done for {loan.loan_id}.")
    return redirect("dashboard_lender")


# -------------------- View / Partial Profile --------------------
@login_required
def view_profile(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    if request.user.role != "lender":
        messages.error(request, "Only lenders can view applicant profiles.")
        return redirect("dashboard_router")

    payment_done = Payment.objects.filter(loan_request=loan, lender=request.user, status__in=["Completed", "Success"]).exists()
    if not payment_done:
        messages.error(request, "⚠️ Complete payment to view full profile.")
        return redirect("dashboard_lender")

    applicant = loan.applicant
    profile = getattr(applicant, "profile", None) or Profile.objects.filter(user=applicant).first()
    applicant_details = getattr(applicant, "applicantdetails", None) or ApplicantDetails.objects.filter(user=applicant).first()

    return render(request, "view_profile.html", {"loan": loan, "applicant": applicant, "profile": profile, "applicant_details": applicant_details})


@login_required
def partial_profile(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    applicant = loan.applicant
    profile = getattr(applicant, "profile", None) or Profile.objects.filter(user=applicant).first()
    applicant_details = getattr(applicant, "applicantdetails", None) or ApplicantDetails.objects.filter(user=applicant).first()
    hidden_fields = ["mobile", "email", "address", "gst_number", "company_name", "business_name", "aadhaar_number"]
    recent_cibil = CibilReport.objects.filter(loan=loan, lender=request.user).order_by("-created_at").first()

    return render(request, "partial_profile.html", {"applicant": applicant, "profile": profile,
        "applicant_details": applicant_details, "loan": loan, "hide_sensitive": True,
        "hidden_fields": hidden_fields, "recent_cibil": recent_cibil})


# -------------------- Forgot / Reset Password --------------------
def forgot_password_view(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = request.build_absolute_uri(reverse('reset_password', args=[uid, token]))
            send_mail("🔑 Reset your password", f"Hi {email}, reset here: {reset_link}", settings.DEFAULT_FROM_EMAIL, [email])
            messages.success(request, "✅ Password reset email sent.")
        except User.DoesNotExist:
            messages.error(request, "❌ Email not found.")
    return render(request, "forgot_password.html")


def reset_password_view(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except:
        user = None
    if user and default_token_generator.check_token(user, token):
        form = SetPasswordForm(user, request.POST or None)
        if request.method == "POST" and form.is_valid():
            form.save()
            messages.success(request, "✅ Password reset successful.")
            return redirect("login")
        return render(request, "reset_password.html", {"form": form})
    messages.error(request, "❌ Invalid or expired link.")
    return redirect("forgot_password")


# -------------------- Support / Complaint / Feedback --------------------
def support_view(request):
    if request.method == "POST":
        form = SupportForm(request.POST)
        if form.is_valid():
            ticket = form.save()
            send_mail(f"[Support] {ticket.subject}", ticket.message, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])
            return render(request, "support.html", {"form": SupportForm(), "success": True})
    else:
        form = SupportForm(initial={"name": getattr(request.user, "profile", None) and request.user.profile.full_name or "",
            "email": request.user.email if request.user.is_authenticated else ""})
    return render(request, "support.html", {"form": form})


def complaint_view(request):
    if request.method == "POST":
        form = ComplaintForm(request.POST)
        if form.is_valid():
            c = form.save()
            send_mail(f"[Complaint] Against {c.complaint_against or 'Unknown'}", c.message, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])
            return render(request, "complaint.html", {"form": ComplaintForm(), "success": True})
    else:
        initial = {}
        if request.user.is_authenticated:
            initial["email"] = request.user.email
            initial["name"] = getattr(request.user.profile, "full_name", "") if getattr(request.user, "profile", None) else ""
            initial["against_role"] = request.user.role if getattr(request.user, "role", None) in ("applicant","lender") else "guest"
        form = ComplaintForm(initial=initial)
    return render(request, "complaint.html", {"form": form})


def feedback_view(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save(commit=False)
            if request.user.is_authenticated:
                fb.user, fb.email, fb.name = request.user, fb.email or request.user.email, fb.name or getattr(request.user.profile, "full_name", "")
            fb.save()
            send_mail(f"[Feedback] {fb.role} rating:{fb.rating}", fb.message, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL])
            return render(request, "feedback.html", {"form": FeedbackForm(), "success": True})
    else:
        initial = {"role": "guest"}
        if request.user.is_authenticated:
            initial.update({"role": request.user.role or "guest", "email": request.user.email, "name": getattr(request.user.profile, "full_name", "")})
        form = FeedbackForm(initial=initial)
    return render(request, "feedback.html", {"form": form})


# -------------------- CIBIL Generate --------------------
@login_required
def generate_cibil_score(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    if request.user.role != "lender":
        return JsonResponse({"ok": False, "message": "Only lenders can generate CIBIL."}, status=403)

    recent = CibilReport.objects.filter(loan=loan, lender=request.user).order_by("-created_at").first()
    if recent and (timezone.now() - recent.created_at) < timedelta(days=30):
        return JsonResponse({"ok": False, "already": True, "score": recent.score, "created_at": recent.created_at.isoformat(),
                             "message": "CIBIL already generated. Try again after 30 days."})

    score = random.randint(300, 900)
    report = CibilReport.objects.create(loan=loan, lender=request.user, score=score)

    applicant_details = loan.applicant.applicant_details
    applicant_details.cibil_score = score
    applicant_details.save(update_fields=["cibil_score"])

    return JsonResponse({"ok": True, "score": report.score, "created_at": report.created_at.isoformat(), "message": "CIBIL generated successfully"})
