from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import (
    authenticate, login, logout, get_user_model
)
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.urls import reverse
from django.conf import settings
from django.utils.dateparse import parse_date


import uuid
from datetime import date

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
            user = User(email=email, role=form_role)
            user.set_password(password)
            user.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("profile_form", user_id=str(user.id))
        except Exception as e:
            messages.error(request, f"Registration error: {e}")
            return redirect(f"/register/?role={form_role}")

    return render(request, "register.html", {"role": role})


# -------------------- Login --------------------
def login_view(request):
    role = (request.GET.get("role") or "").lower()

    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        password = request.POST.get("password") or ""
        form_role = (request.POST.get("role") or role).lower()

        user = authenticate(request, email=email, password=password) or \
               authenticate(request, username=email, password=password)

        if user:
            if form_role and getattr(user, "role", None) != form_role:
                messages.error(request, "Role mismatch")
                return redirect(f"/login/?role={form_role}")

            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("profile_form", user_id=str(user.id)) if not is_profile_complete(user) else redirect("dashboard_router")
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
        return redirect("index")

    role = (user.role or "").lower()
    profile = getattr(user, "profile", None) or Profile.objects.filter(user=user).first()
    applicant_details = ApplicantDetails.objects.filter(user=user).first() if role == "applicant" else None
    lender_details = LenderDetails.objects.filter(user=user).first() if role == "lender" else None

    def G(*keys):
        for k in keys:
            v = request.POST.get(k)
            if v and str(v).strip():
                return str(v).strip()
        return None

    if request.method == "POST":
        if not profile:
            profile = Profile(user=user)
        profile.full_name = G("full_name", "fullName") or ""
        profile.mobile = G("mobile") or ""
        dob_val = G("dob")
        profile.dob = parse_date(dob_val) if dob_val else None
        profile.gender = G("gender")
        profile.marital_status = G("marital_status", "maritalStatus")
        profile.address = G("address")
        profile.pincode = G("pincode")
        profile.city = G("city")
        profile.state = G("state")
        pancard_number = G("pancard_number", "panCardNumber")
        if not pancard_number:
            messages.error(request, "PAN Card Number is required.")
            return render(request, "profile_form.html", {"user": user, "profile": profile, "role": role})
        profile.pancard_number = pancard_number
        profile.aadhaar_number = G("aadhaar_number", "aadhaarNumber")
        profile.save()

        if role == "applicant":
            details, _ = ApplicantDetails.objects.get_or_create(user=user)
            details.employment_type = G("employment_type", "employmentType")
            details.cibil_score = G("cibil_score")
            if details.employment_type == "Business":
                details.business_name = G("business_name", "businessName")
                details.business_type = G("business_type", "businessType")
                details.business_sector = G("business_sector", "businessSector")
                details.total_turnover = G("total_turnover", "totalTurnover")
                details.last_year_turnover = G("last_year_turnover", "lastYearTurnover")
                details.business_total_emi = G("business_total_emi", "businessTotalEmi")
                details.business_itr_status = G("business_itr_status", "businessItrStatus")
                details.company_name = details.company_type = details.designation = None
                details.current_salary = details.other_income = details.total_emi = details.itr = None
            else:
                details.company_name = G("company_name", "companyName")
                details.company_type = G("company_type", "companyType")
                details.designation = G("designation")
                details.current_salary = G("current_salary", "currentSalary")
                details.other_income = G("other_income", "otherIncome")
                details.total_emi = G("total_emi", "totalEmi")
                details.itr = G("itr")
                details.business_name = details.business_type = details.business_sector = None
                details.total_turnover = details.last_year_turnover = details.business_total_emi = details.business_itr_status = None
            details.save()
            applicant_details = details

        elif role == "lender":
            l, _ = LenderDetails.objects.get_or_create(user=user)
            l.lender_type = G("lender_type")
            l.bank_firm_name = G("bank_firm_name", "bankfirmName")
            l.branch_name = G("branch_name", "branchName")
            l.dsa_code = G("dsa_code", "dsaCode")
            l.designation = G("designation")
            l.gst_number = G("gst_number", "gstNumber")
            l.save()
            lender_details = l

        messages.success(request, "✅ Profile saved successfully.")
        return redirect("dashboard_router")

    return render(request, "profile_form.html", {
        "user": user,
        "profile": profile,
        "role": role.capitalize() if role else "",
        "applicant_details": applicant_details,
        "lender_details": lender_details,
    })

# -------------------- Admin Login --------------------
def admin_login(request):
    """
    Custom admin login page.
    Accepts 'identifier' (email or mobile) and password.
    Only allows superusers (admins) to login here.
    """
    if request.method == "POST":
        identifier = (request.POST.get("identifier") or "").strip()
        password = request.POST.get("password") or ""

        user = None
        if identifier:
            # Try email first
            user = User.objects.filter(email__iexact=identifier).first()

            # If not found by email, try profile.mobile
            if not user:
                user = User.objects.filter(profile__mobile=identifier).first()

        if user:
            # Authenticate only with username (email is username in custom user)
            auth_user = authenticate(request, username=user.email, password=password)
            if auth_user and auth_user.is_superuser:
                login(request, auth_user)
                return redirect("dashboard_admin")
            else:
                messages.error(request, "❌ Invalid password or not an admin user.")
        else:
            messages.error(request, "❌ User not found.")

    return render(request, "admin_login.html")

# -------------------- Admin Dashboard --------------------
@login_required
def dashboard_admin(request):
    """
    Admin dashboard view — only superusers allowed.
    Provides lists for: all users, applicants, lenders, loans, payments.
    """
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admins only.")
        return redirect("index")

    # 🔹 All users (applicants + lenders) ordered by created_at if field exists
    if "created_at" in [f.name for f in User._meta.fields]:
        users_qs = User.objects.all().order_by("-created_at")
    else:
        users_qs = User.objects.all().order_by("-id")

    # 🔹 ApplicantDetails & LenderDetails
    applicants = ApplicantDetails.objects.select_related("user").all().order_by("-id")
    lenders = LenderDetails.objects.select_related("user").all().order_by("-id")

    # 🔹 Loans & Payments
    loans = LoanRequest.objects.select_related("applicant", "accepted_lender").all().order_by("-created_at")
    payments = Payment.objects.select_related("lender", "loan_request").all().order_by("-id")

    # 🔹 Context for template
    context = {
        "users": users_qs,
        "applicants": applicants,
        "lenders": lenders,
        "loans": loans,
        "payments": payments,
    }
    return render(request, "dashboard_admin.html", context)


# -------------------- Admin: User action (activate / deactivate / delete) --------------------
@login_required
@require_POST
@csrf_protect
def admin_user_action(request, user_id):
    """
    AJAX endpoint for admin actions on users: activate / deactivate / delete.
    Returns JSON for AJAX; redirects with messages if not AJAX.
    """
    if not request.user.is_superuser:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "message": "Access denied."}, status=403)
        messages.error(request, "Access denied.")
        return redirect("dashboard_admin")

    action = (request.POST.get("action") or "").strip().lower()
    reason = (request.POST.get("reason") or "").strip()[:1000]

    try:
        target = User.objects.get(id=user_id)
    except (User.DoesNotExist, ValueError, TypeError):
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "message": "User not found."}, status=404)
        messages.error(request, "User not found.")
        return redirect("dashboard_admin")

    support_from = getattr(settings, "DEFAULT_FROM_EMAIL", "support@loansaathihub.in")
    orig_email = target.email

    # Helper to send mail (fail silently)
    def _send(subject, body, to_email):
        try:
            send_mail(subject, body, support_from, [to_email], fail_silently=True)
        except Exception:
            # swallow to avoid crashing the admin action
            pass

    # ----- Deactivate -----
    if action == "deactivate":
        target.is_active = False
        target.save()

        # mark profile flag if exists
        profile = getattr(target, "profile", None)
        if profile:
            try:
                profile.is_blocked = True
                profile.save()
            except Exception:
                pass

        subject = "Action Required: Your Account May Be Deactivated Due to Misuses"
        body = (
            f"Dear {getattr(target, 'first_name', '') or orig_email},\n\n"
            "Warning: Your account on Loan Saathi Hub has been temporarily DEACTIVATED due to reported misuse or policy violation.\n\n"
            f"Reason: {reason or 'Policy violation'}\n\n"
            "If you believe this is a mistake, please contact our support team at support@loansaathihub.in.\n\n"
            "Regards,\nLoan Saathi Hub Support\n"
        )
        _send(subject, body, orig_email)
        resp = {"ok": True, "message": "User deactivated and email sent."}

    # ----- Activate -----
    elif action == "activate":
        target.is_active = True
        target.save()
        profile = getattr(target, "profile", None)
        if profile:
            try:
                profile.is_blocked = False
                profile.save()
            except Exception:
                pass

        subject = "Your Account Activated — Loan Saathi Hub"
        body = (
            f"Dear {getattr(target, 'first_name', '') or orig_email},\n\n"
            "Congratulations! Your Loan Saathi Hub account has been re-activated. Please follow the platform's guidelines to avoid future actions.\n\n"
            "Regards,\nLoan Saathi Hub Support\n"
        )
        _send(subject, body, orig_email)
        resp = {"ok": True, "message": "User activated and email sent."}

    # ----- Delete (soft disable + obfuscate email) -----
    elif action == "delete":
        try:
            target.is_active = False
            # store original email to notify
            original = orig_email
            target.email = f"disabled+{target.id}@blocked.loansaathihub"
            if hasattr(target, "username"):
                target.username = f"disabled_{target.id}"
            target.save()
        except Exception:
            pass

        subject = "Account Permanently Disabled"
        body = (
            f"Dear {getattr(target, 'first_name', '') or orig_email},\n\n"
            "Warning: Your account has been permanently blocked due to misuse of the platform. This action is irreversible.\n\n"
            "If you think this is an error, contact support@loansaathihub.in.\n\n"
            "Regards,\nLoan Saathi Hub Support\n"
        )
        _send(subject, body, orig_email)
        resp = {"ok": True, "message": "User permanently disabled and email sent."}

    else:
        resp = {"ok": False, "message": "Unknown action."}
        # return 400 for AJAX
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse(resp, status=400)
        messages.error(request, resp["message"])
        return redirect("dashboard_admin")

    # Return JSON for AJAX requests (fetch), fallback to redirect with message
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(resp)
    else:
        messages.success(request, resp.get("message", "Action processed."))
        return redirect("dashboard_admin")


# -------------------- Admin Logout --------------------
@login_required
def admin_logout(request):
    logout(request)
    messages.success(request, "✅ Admin logged out successfully")
    return redirect("admin_login")

# -------------------- Dashboard Router --------------------
@login_required
def dashboard_router(request):
    if getattr(request.user, "role", None) == "lender":
        return redirect("dashboard_lender")
    elif getattr(request.user, "role", None) == "applicant":
        return redirect("dashboard_applicant")
    elif request.user.is_superuser:
        return redirect("dashboard_admin")
    else:
        return redirect("index")


# -------------------- Dashboard Applicant --------------------
@login_required
def dashboard_applicant(request):
    loans = LoanRequest.objects.filter(applicant=request.user).prefetch_related("lender_statuses").order_by("-created_at")

    # Loan status calculation
    for loan in loans:
        # Map Accepted → Approved, Finalised → Rejected
        if loan.status == "Accepted":
            loan.global_status = "Approved"
            loan.global_remarks = "You accepted this lender."
        elif loan.status == "Finalised":
            loan.global_status = "Rejected"
            loan.global_remarks = "Finalised by Applicant"
        else:
            statuses = loan.lender_statuses.all() if hasattr(loan, "lender_statuses") else LoanLenderStatus.objects.filter(loan=loan)
            if not statuses or all(ls.status == "Pending" for ls in statuses):
                loan.global_status = "Pending"
                loan.global_remarks = "Lender Reviewing Your Loan"
            elif any(ls.status == "Approved" for ls in statuses):
                loan.global_status = "Approved"
                loan.global_remarks = "Lender Reviewing Your Loan"
            elif all(ls.status == "Rejected" for ls in statuses):
                loan.global_status = "Rejected"
                loan.global_remarks = "Lender Reviewing Your Loan"
            else:
                loan.global_status = "Pending"
                loan.global_remarks = "Lender Reviewing Your Loan"

    today = date.today()
    total_today = loans.filter(created_at__date=today).count()
    total_approved = loans.filter(status__in=["Approved", "Accepted"]).count()   # ✅ Accepted treated as Approved
    total_rejected = loans.filter(status__in=["Rejected", "Finalised"]).count()  # ✅ Finalised treated as Rejected
    total_pending = loans.filter(status="Pending").count()

    return render(request, "dashboard_applicant.html", {
        "loans": loans,
        "total_today": total_today,
        "total_approved": total_approved,
        "total_rejected": total_rejected,
        "total_pending": total_pending,
    })


# -------------------- Dashboard Lender --------------------
@login_required
def dashboard_lender(request):
    profile = getattr(request.user, "profile", None)

    lender_feedbacks = (
        LoanLenderStatus.objects.filter(lender=request.user)
        .select_related("loan", "loan__applicant")
        .order_by("-updated_at")
    )

    # Map Accepted → Approved, Finalised → Rejected
    for fb in lender_feedbacks:
        if fb.loan.status == "Accepted":
            fb.loan.global_status = "Approved"
        elif fb.loan.status == "Finalised":
            fb.loan.global_status = "Rejected"
        else:
            fb.loan.global_status = fb.loan.status

    today = timezone.now().date()
    total_today = lender_feedbacks.filter(loan__created_at__date=today).count()
    total_approved = lender_feedbacks.filter(loan__status__in=["Approved", "Accepted"]).count()
    total_rejected = lender_feedbacks.filter(loan__status__in=["Rejected", "Finalised"]).count()
    total_pending = lender_feedbacks.filter(loan__status="Pending").count()

    # Unhandled pending loans
    handled_loans = LoanLenderStatus.objects.values_list("loan_id", flat=True)
    pending_loans = (
        LoanRequest.objects.filter(status="Pending")
        .exclude(id__in=handled_loans)
        .select_related("applicant")
        .order_by("-created_at")
    )

    # Finalised loans (Accepted bhi yaha aayenge)
    finalised_loans = (
        LoanRequest.objects.filter(status__in=["Accepted", "Finalised"])
        .select_related("applicant", "accepted_lender")
    )

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

    # Finalize loan
    loan.status = "Accepted"
    loan.accepted_lender = lender
    loan.save()

    messages.success(request, "✅ You have accepted this lender. Other lenders can no longer access this loan.")
    return redirect("dashboard_applicant")

# -------------------- Loan Request --------------------
@login_required
def loan_request(request):
    if request.method == "POST" and getattr(request.user, "role", None) == "applicant":
        loan_id = "LSH" + get_random_string(6, allowed_chars="0123456789")
        loan = LoanRequest.objects.create(
            id=uuid.uuid4(),
            loan_id=loan_id,
            applicant=request.user,
            loan_type=request.POST.get("loan_type") or "",
            amount_requested=request.POST.get("amount_requested") or 0,
            duration_months=request.POST.get("duration_months") or 0,
            interest_rate=request.POST.get("interest_rate") or 0,
            reason_for_loan=request.POST.get("reason_for_loan") or "",
            status="Pending"
        )
        for lender in User.objects.filter(role="lender"):
            LoanLenderStatus.objects.create(
                loan=loan,
                lender=lender,
                status="Pending",
                remarks=loan.reason_for_loan or "Lender Reviewing Your Loan",
            )
        messages.success(request, f"✅ Loan request {loan.loan_id} submitted successfully.")
        return redirect("dashboard_router")
    return render(request, "loan_request.html")


# -------------------- Approve / Reject --------------------
@login_required
def reject_loan(request, loan_id):
    if request.method == "POST":
        reason = request.POST.get("reason")
        loan = get_object_or_404(LoanRequest, id=loan_id)

        lender_status = get_object_or_404(LoanLenderStatus, loan=loan, lender=request.user)
        lender_status.status = "Rejected"
        lender_status.remarks = reason
        lender_status.save()

        messages.warning(request, f"Loan {loan.loan_id} rejected with reason: {reason}")
        return redirect("dashboard_lender")


@login_required
def approve_loan(request, loan_id):
    ls = get_object_or_404(LoanLenderStatus, loan__id=loan_id, lender=request.user)
    ls.status = "Approved"
    ls.remarks = "Payment done, Loan Approved"
    ls.save()
    messages.success(request, f"Loan {ls.loan.loan_id} approved successfully!")
    return redirect("dashboard_lender")

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
        # Common Profile
        profile.full_name = request.POST.get("fullName")
        profile.mobile = request.POST.get("mobile")
        profile.gender = request.POST.get("gender")
        profile.marital_status = request.POST.get("maritalStatus")
        profile.address = request.POST.get("address")
        profile.pincode = request.POST.get("pincode")
        profile.city = request.POST.get("city")
        profile.state = request.POST.get("state")

        pancard_number = request.POST.get("pancardNumber")
        if pancard_number:
            profile.pancard_number = pancard_number
        profile.aadhaar_number = request.POST.get("aadhaarNumber")
        profile.dob = request.POST.get("dob") or None
        profile.save()

        # Applicant details
        if user.role == "applicant":
            applicant_details.job_type = request.POST.get("jobType")
            applicant_details.cibil_score = request.POST.get("cibilScore")
            applicant_details.employment_type = request.POST.get("employmentType")

            # Job fields
            applicant_details.company_name = request.POST.get("companyName")
            applicant_details.company_type = request.POST.get("companyType")
            applicant_details.designation = request.POST.get("designation")
            applicant_details.itr = request.POST.get("itrJob")
            applicant_details.current_salary = request.POST.get("currentSalary") or None
            applicant_details.other_income = request.POST.get("otherIncome") or None
            applicant_details.total_emi = request.POST.get("totalEmiJob") or None

            # Business fields
            applicant_details.business_name = request.POST.get("businessName")
            applicant_details.business_type = request.POST.get("businessType")
            applicant_details.business_sector = request.POST.get("businessSector")
            applicant_details.total_turnover = request.POST.get("turnover3y") or None
            applicant_details.last_year_turnover = request.POST.get("turnover1y") or None
            applicant_details.business_total_emi = request.POST.get("totalEmiBusiness") or None
            applicant_details.business_itr_status = request.POST.get("itrBusiness")

            applicant_details.save()
            messages.success(request, "✅ Applicant profile updated successfully")
            return redirect("dashboard_applicant")

        # Lender details
        elif user.role == "lender":
            lender_details.lender_type = request.POST.get("lenderType")
            lender_details.dsa_code = request.POST.get("dsaCode")
            lender_details.bank_firm_name = request.POST.get("firmName")
            lender_details.gst_number = request.POST.get("gstNumber")
            lender_details.branch_name = request.POST.get("branchName")
            lender_details.designation = request.POST.get("designation")
            lender_details.save()
            messages.success(request, "✅ Lender profile updated successfully")
            return redirect("dashboard_lender")

    return render(
        request,
        "edit_profile.html",
        {
            "user": user,
            "profile": profile,
            "role": user.role.capitalize(),
            "applicant_details": applicant_details,
            "lender_details": lender_details,
        },
    )


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
            status="Completed",
        )
        ls = get_object_or_404(LoanLenderStatus, loan=loan, lender=request.user)
        ls.status = "Approved"
        ls.remarks = "Payment done, Loan Approved"
        ls.save()
        messages.success(request, f"✅ Loan {loan.loan_id} approved after payment.")
        return redirect("dashboard_lender")
    return render(request, "payment.html", {"loan": loan})


@login_required
def make_dummy_payment(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    Payment.objects.create(
        loan_request=loan,
        lender=request.user,
        amount=loan.amount_requested,
        status="Completed",
        payment_method="Dummy"
    )
    ls = get_object_or_404(LoanLenderStatus, loan=loan, lender=request.user)
    ls.status = "Approved"
    ls.remarks = "Dummy Payment done"
    ls.save()
    messages.success(request, f"✅ Dummy Payment done. Loan {loan.loan_id} marked as Approved.")
    return redirect("dashboard_lender")


# -------------------- View Profile --------------------
@login_required
def view_profile(request, loan_id):
    # Loan aur applicant fetch
    loan = get_object_or_404(LoanRequest, id=loan_id)
    applicant = loan.applicant

    # ✅ Sirf lenders ke liye allow
    if request.user.role != "lender":
        messages.error(request, "⚠️ Only lenders can view applicant profiles.")
        return redirect("dashboard_router")

    # ✅ Payment check (Completed ya Success status required)
    payment_done = Payment.objects.filter(
        loan_request=loan,
        lender=request.user,
        status__in=["Completed", "Success"]
    ).exists()

    if not payment_done:
        messages.error(
            request,
            "⚠️ You can only view applicant's full profile after completing payment."
        )
        return redirect("dashboard_lender")

    # ✅ Safe profile + applicant details fetch
    profile = getattr(applicant, "profile", None)
    if not profile:
        profile = Profile.objects.filter(user=applicant).first()

    applicant_details = getattr(applicant, "applicantdetails", None)
    if not applicant_details:
        applicant_details = ApplicantDetails.objects.filter(user=applicant).first()

    # ✅ Context pass
    return render(request, "view_profile.html", {
        "loan": loan,
        "applicant": applicant,
        "profile": profile,
        "applicant_details": applicant_details,
        "hide_sensitive": False,  # future toggle agar partial profile dikhani ho
    })



# -------------------- Partial Profile --------------------
@login_required
def partial_profile(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    applicant = loan.applicant

    profile = getattr(applicant, "profile", None) or Profile.objects.filter(user=applicant).first()
    applicant_details = getattr(applicant, "applicantdetails", None) or ApplicantDetails.objects.filter(user=applicant).first()

    hidden_fields = [
        "mobile", "email", "address",
        "gst_number", "company_name",
        "business_name", "aadhaar_number"
    ]

    return render(request, "partial_profile.html", {
        "applicant": applicant,
        "profile": profile,
        "applicant_details": applicant_details,
        "loan": loan,
        "hide_sensitive": True,
        "hidden_fields": hidden_fields,
    })


# -------------------- Forgot / Reset Password --------------------
def forgot_password_view(request):
    if request.method == "POST":
        email = (request.POST.get("email") or "").strip().lower()
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = request.build_absolute_uri(reverse('reset_password', args=[uid, token]))
            subject = "🔑 Reset your Loan Saathi Hub password"
            message = f"Hi {email},\n\nClick the link to reset your password:\n👉 {reset_link}"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
            messages.success(request, "✅ Password reset email sent.")
        except User.DoesNotExist:
            messages.error(request, "❌ Email not found.")
    return render(request, "forgot_password.html")


def reset_password_view(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
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

# ---------- Support page ----------
def support_view(request):
    if request.method == "POST":
        form = SupportForm(request.POST)
        if form.is_valid():
            ticket = form.save()
            # send email to support
            subject = f"[Support] {ticket.subject}"
            body = f"Support ticket from {ticket.name or 'Guest'} <{ticket.email}>\n\nMessage:\n{ticket.message}\n\nTicket ID: {ticket.id}"
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL], fail_silently=True)
            return render(request, "support.html", {"form": SupportForm(), "success": True})
    else:
        form = SupportForm(initial={
            "name": getattr(request.user, "profile", None) and request.user.profile.full_name or "",
            "email": request.user.email if request.user.is_authenticated else ""
        })
    return render(request, "support.html", {"form": form})


# ---------- Complaint page ----------
def complaint_view(request):
    if request.method == "POST":
        form = ComplaintForm(request.POST)
        if form.is_valid():
            c = form.save()
            # email to support
            subject = f"[Complaint] Against {c.complaint_against or 'Unknown'}"
            body = f"Complaint from {c.name or 'Guest'} <{c.email}>\nAgainst: {c.complaint_against}\nRole: {c.against_role}\n\nMessage:\n{c.message}\n\nID: {c.id}"
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL], fail_silently=True)
            return render(request, "complaint.html", {"form": ComplaintForm(), "success": True})
    else:
        initial = {}
        if request.user.is_authenticated:
            initial["email"] = request.user.email
            initial["name"] = getattr(request.user.profile, "full_name", "") if getattr(request.user, "profile", None) else ""
            # if logged in set role
            initial["against_role"] = request.user.role if getattr(request.user, "role", None) in ("applicant","lender") else "guest"
        form = ComplaintForm(initial=initial)
    return render(request, "complaint.html", {"form": form})


# ---------- Feedback page ----------
def feedback_view(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            fb = form.save(commit=False)
            if request.user.is_authenticated:
                fb.user = request.user
                fb.email = fb.email or request.user.email
                fb.name = fb.name or getattr(request.user.profile, "full_name", "")
            fb.save()
            # optionally email a copy
            subject = f"[Feedback] {fb.role} rating:{fb.rating or 'n/a'}"
            body = f"Feedback from {fb.name or 'Guest'} <{fb.email or 'n/a'}>\nRole: {fb.role}\nRating: {fb.rating}\n\n{fb.message}\n\nID: {fb.id}"
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL], fail_silently=True)
            return render(request, "feedback.html", {"form": FeedbackForm(), "success": True})
    else:
        initial = {"role": "guest"}
        if request.user.is_authenticated:
            initial["role"] = request.user.role or "guest"
            initial["email"] = request.user.email
            initial["name"] = getattr(request.user.profile, "full_name", "")
        form = FeedbackForm(initial=initial)
    return render(request, "feedback.html", {"form": form})
