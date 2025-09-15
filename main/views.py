from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from django.utils.dateparse import parse_date
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import SetPasswordForm
from django.conf import settings
from django.urls import reverse
from datetime import date
import uuid
from django.utils import timezone
from django.views.decorators.http import require_POST


from .models import (
    User,
    Profile,
    ApplicantDetails,
    LenderDetails,
    LoanRequest,
    LoanLenderStatus,
    Payment
)

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

# -------------------- Admin Custom Login --------------------
def admin_login(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")
        password = request.POST.get("password")

        user = None
        # identifier can be email or mobile
        try:
            user = User.objects.get(email=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(profile__mobile=identifier)
            except User.DoesNotExist:
                pass

        if user:
            auth_user = authenticate(request, email=user.email, password=password) or \
                        authenticate(request, username=user.email, password=password)
            if auth_user and (auth_user.is_staff or auth_user.is_superuser):
                login(request, auth_user, backend="django.contrib.auth.backends.ModelBackend")
                return redirect("dashboard_admin")
        messages.error(request, "❌ Invalid credentials or not authorized for admin access.")

    return render(request, "admin_login.html")


# -------------------- Admin Dashboard --------------------
@login_required
def dashboard_admin(request):
    # only superuser
    if not request.user.is_superuser:
        messages.error(request, "Access denied. Admins only.")
        return redirect("index")

    # users: all registered (applicant + lender)
    users_qs = User.objects.all().order_by("-created_at")  # generic

    applicants = ApplicantDetails.objects.select_related("user").all().order_by("-id")
    lenders = LenderDetails.objects.select_related("user").all().order_by("-id")
    loans = LoanRequest.objects.all().order_by("-created_at")
    payments = Payment.objects.select_related("lender", "loan_request").all().order_by("-id")

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
def admin_user_action(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({"ok": False, "message": "Access denied."}, status=403)

    action = request.POST.get("action")  # values: activate, deactivate, delete
    reason = request.POST.get("reason", "")[:1000]  # optional admin reason

    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"ok": False, "message": "User not found."}, status=404)

    # Common vars for mails
    support_from = "support@loansaathihub.in"
    ctx = {"user": target, "admin": request.user, "reason": reason}

    if action == "deactivate":
        target.is_active = False
        # optionally mark some flag on profile if exists
        profile = getattr(target, "profile", None)
        if profile:
            try:
                profile.is_blocked = True
                profile.save()
            except Exception:
                pass
        target.save()

        # send email to user
        subject = "Action Required: Your Account May Be Deactivated Due to Misuses"
        body = (
            f"Dear {getattr(target, 'first_name', '') or target.email},\n\n"
            "Warning: Your account on Loan Saathi Hub has been temporarily DEACTIVATED due to reported misuse or policy violation.\n\n"
            "If you believe this is a mistake, please contact our support team immediately at support@loansaathihub.in with your account details and any supporting information.\n\n"
            "Regards,\nLoan Saathi Hub Support\n"
        )
        try:
            send_mail(subject, body, support_from, [target.email], fail_silently=True)
        except Exception:
            pass

        return JsonResponse({"ok": True, "message": "User deactivated and email sent."})

    elif action == "activate":
        target.is_active = True
        profile = getattr(target, "profile", None)
        if profile:
            try:
                profile.is_blocked = False
                profile.save()
            except Exception:
                pass
        target.save()

        subject = "Your Account Activated — Loan Saathi Hub"
        body = (
            f"Dear {getattr(target, 'first_name', '') or target.email},\n\n"
            "Congratulations! Your Loan Saathi Hub account has been re-activated. Please ensure you follow the platform's guidelines to avoid future actions.\n\n"
            "Regards,\nLoan Saathi Hub Support\n"
        )
        try:
            send_mail(subject, body, support_from, [target.email], fail_silently=True)
        except Exception:
            pass

        return JsonResponse({"ok": True, "message": "User activated and email sent."})

    elif action == "delete":
        # We will 'disable' the account permanently: mark inactive and obfuscate email
        orig_email = target.email
        try:
            target.is_active = False
            # obfuscate email to prevent reuse/login
            target.email = f"disabled+{target.id}@blocked.loansaathihub"
            target.username = None if hasattr(target, "username") else getattr(target, "username", None)
            target.save()
        except Exception:
            pass

        subject = "Account Permanently Disabled"
        body = (
            f"Dear {getattr(target, 'first_name', '') or orig_email},\n\n"
            "Warning: Your account has been permanently blocked due to misuse of the platform. If you think this is an error, please contact support@loansaathihub.in.\n\n"
            "This action is irreversible.\n\n"
            "Regards,\nLoan Saathi Hub Support\n"
        )
        try:
            send_mail(subject, body, support_from, [orig_email], fail_silently=True)
        except Exception:
            pass

        return JsonResponse({"ok": True, "message": "User permanently disabled and email sent."})

    else:
        return JsonResponse({"ok": False, "message": "Unknown action."}, status=400)

# -------------------- Admin Logout --------------------
@login_required
def admin_logout(request):
    logout(request)
    messages.success(request, "✅ Admin logged out successfully")
    return redirect("admin_login")


# -------------------- Dashboard Router --------------------
@login_required
def dashboard_router(request):
    return redirect("dashboard_lender") if getattr(request.user, "role", None) == "lender" else redirect("dashboard_applicant")


# -------------------- Dashboard Applicant --------------------
@login_required
def dashboard_applicant(request):
    loans = LoanRequest.objects.filter(applicant=request.user).prefetch_related("lender_statuses").order_by("-created_at")

    # Loan status calculation
    for loan in loans:
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
    total_today = LoanRequest.objects.filter(applicant=request.user, created_at__date=today).count()
    total_approved = LoanRequest.objects.filter(applicant=request.user, status="Approved").count()
    total_rejected = LoanRequest.objects.filter(applicant=request.user, status="Rejected").count()
    total_pending = LoanRequest.objects.filter(applicant=request.user, status="Pending").count()

    return render(request, "dashboard_applicant.html", {
        "loans": loans,
        "total_today": total_today,
        "total_approved": total_approved,
        "total_rejected": total_rejected,
        "total_pending": total_pending,
    })

# -------------------- Dashboard Applicant -Accept / Hold-----------------
@login_required
def applicant_accept_loan(request, loan_id, lender_id):
    loan = get_object_or_404(LoanRequest, id=loan_id, applicant=request.user)
    lender = get_object_or_404(User, id=lender_id, role="lender")

    # loan finalise
    loan.status = "Accepted"
    loan.accepted_lender = lender
    loan.save()

    messages.success(request, "After Accepted this loan will no more for Lenders.")
    return redirect("dashboard_applicant")


@login_required
def applicant_hold_loan(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id, applicant=request.user)

    loan.status = "Hold"
    loan.save()

    messages.info(request, "Loan request is on Hold. Lenders cannot proceed until you Accept.")
    return redirect("dashboard_applicant")


# -------------------- Dashboard Lender --------------------
@login_required
def dashboard_lender(request):
    profile = getattr(request.user, "profile", None)

    # Lender ke apne feedbacks (lekin finalised loans exclude kar diye)
    lender_feedbacks = (
        LoanLenderStatus.objects.filter(lender=request.user)
        .exclude(loan__status__in=["Accepted", "Hold"])  # ✅ yaha filter lagaya
        .select_related("loan", "loan__applicant")
    )

    today = timezone.now().date()
    total_today = lender_feedbacks.filter(loan__created_at__date=today).count()
    total_approved = lender_feedbacks.filter(status="Approved").count()
    total_rejected = lender_feedbacks.filter(status="Rejected").count()
    total_pending = lender_feedbacks.filter(status="Pending").count()

    # Sare applicants ke unhandled pending loans
    handled_loans = LoanLenderStatus.objects.values_list("loan_id", flat=True)
    pending_loans = (
        LoanRequest.objects.filter(status="Pending")
        .exclude(id__in=handled_loans)
        .select_related("applicant")
        .order_by("-created_at")
    )

    # Applicant ke finalised loans (Accepted ya Hold)
    finalised_loans = (
        LoanRequest.objects.filter(status__in=["Accepted", "Hold"])
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
    loan = get_object_or_404(LoanRequest, id=loan_id)
    applicant = loan.applicant

    payment_done = Payment.objects.filter(
        loan_request=loan, lender=request.user, status="Completed"
    ).exists()

    if not payment_done:
        messages.error(request, "⚠️ You can only view applicant's full profile after payment is done.")
        return redirect("dashboard_lender")

    profile = getattr(applicant, "profile", None) or Profile.objects.filter(user=applicant).first()
    applicant_details = getattr(applicant, "applicantdetails", None) or ApplicantDetails.objects.filter(user=applicant).first()

    return render(request, "view_profile.html", {
        "applicant": applicant,
        "profile": profile,
        "applicant_details": applicant_details,
        "loan": loan,
        "hide_sensitive": False,
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
