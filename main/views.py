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
from .models import LoanRequest, LoanLenderStatus, Payment
from django.utils.timezone import now
from datetime import date

from .models import (
    User,
    Profile,
    ApplicantDetails,
    LenderDetails,
    LoanRequest,
    Payment,
)
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
        # ----- Common Profile -----
        profile.full_name = request.POST.get("fullName")
        profile.mobile = request.POST.get("mobile")
        profile.gender = request.POST.get("gender")
        profile.marital_status = request.POST.get("maritalStatus")
        profile.address = request.POST.get("address")
        profile.pincode = request.POST.get("pincode")
        profile.city = request.POST.get("city")
        profile.state = request.POST.get("state")
        profile.pan_number = request.POST.get("panNumber")
        profile.aadhar = request.POST.get("aadharNumber")
        profile.dob = request.POST.get("dob") or None
        profile.save()

        # ----- Applicant -----
        if user.role == "applicant":
            details, _ = ApplicantDetails.objects.get_or_create(user=user)
            details.job_type = request.POST.get("jobType")
            details.cibil_score = request.POST.get("cibilScore")
            details.employment_type = request.POST.get("employmentType")

            # Job fields
            details.company_name = request.POST.get("companyName")
            details.company_type = request.POST.get("companyType")
            details.designation = request.POST.get("designation")
            details.itr = request.POST.get("itrJob")
            details.current_salary = request.POST.get("currentSalary") or None
            details.other_income = request.POST.get("otherIncome") or None
            details.total_emi = request.POST.get("totalEmiJob") or None

            # Business fields
            details.business_name = request.POST.get("businessName")
            details.business_type = request.POST.get("businessType")
            details.business_sector = request.POST.get("businessSector")
            details.total_turnover = request.POST.get("turnover3y") or None
            details.last_year_turnover = request.POST.get("turnover1y") or None
            details.business_total_emi = request.POST.get("totalEmiBusiness") or None
            details.business_itr_status = request.POST.get("itrBusiness")

            details.save()
            messages.success(request, "✅ Applicant profile completed successfully")
            return redirect("dashboard_applicant")

        # ----- Lender -----
        elif user.role == "lender":
            details, _ = LenderDetails.objects.get_or_create(user=user)
            details.lender_type = request.POST.get("lenderType")
            details.dsa_code = request.POST.get("dsaCode")
            details.bank_firm_name = request.POST.get("firmName")
            details.gst_number = request.POST.get("gstNumber")
            details.branch_name = request.POST.get("branchName")
            details.designation = request.POST.get("designation")
            details.save()
            messages.success(request, "✅ Lender profile completed successfully")
            return redirect("dashboard_lender")

    return render(request, "profile_form.html", {"user": user, "role": user.role.capitalize()})

# -------------------- Edit Profile --------------------
@login_required
def edit_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.user.id != user.id and not request.user.is_superuser:
        messages.error(request, "You are not allowed to edit this profile.")
        return redirect("home")

    profile, _ = Profile.objects.get_or_create(user=user)
    applicant_details = None
    lender_details = None

    if user.role == "applicant":
        applicant_details, _ = ApplicantDetails.objects.get_or_create(user=user)
    elif user.role == "lender":
        lender_details, _ = LenderDetails.objects.get_or_create(user=user)

    if request.method == "POST":
        # ----- Common Profile -----
        profile.full_name = request.POST.get("fullName")
        profile.mobile = request.POST.get("mobile")
        profile.gender = request.POST.get("gender")
        profile.marital_status = request.POST.get("maritalStatus")
        profile.address = request.POST.get("address")
        profile.pincode = request.POST.get("pincode")
        profile.city = request.POST.get("city")
        profile.state = request.POST.get("state")
        profile.pan_number = request.POST.get("panNumber")
        profile.aadhar = request.POST.get("aadharNumber")
        profile.dob = request.POST.get("dob") or None
        profile.save()

        # ----- Applicant -----
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

        # ----- Lender -----
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


@login_required
def dashboard_applicant(request):
    loans = LoanRequest.objects.filter(applicant=request.user).prefetch_related("lender_statuses").order_by("-created_at")

    for loan in loans:
        statuses = loan.lender_statuses.all()

        if not statuses or all(ls.status == "Pending" for ls in statuses):
            loan.global_status = "Pending"
            loan.global_remark = "Lender Reviewing Your Loan"
        elif any(ls.status == "Approved" for ls in statuses):
            loan.global_status = "Approved"
            loan.global_remark = "Lender Reviewing Your Loan"
        elif all(ls.status == "Rejected" for ls in statuses):
            loan.global_status = "Rejected"
            loan.global_remark = "Lender Reviewing Your Loan"
        else:
            loan.global_status = "Pending"
            loan.global_remark = "Lender Reviewing Your Loan"

    return render(request, "dashboard_applicant.html", {"loans": loans})


# -------------------- Lender Dashboard --------------------
@login_required
def dashboard_lender(request):
    """
    Lender dashboard showing all loans (pending + history).
    Every lender (new/old) should see all pending loan requests.
    """

    # Fetch all loan requests (newest first)
    all_loans = LoanRequest.objects.order_by('-created_at')

    # Filter only pending loans (for new lenders also)
    pending_loans = LoanRequest.objects.filter(status="Pending").order_by('-created_at')

    # Summary counts
    today = date.today()
    total_today = LoanRequest.objects.filter(created_at__date=today).count()
    total_approved = LoanRequest.objects.filter(status='Approved').count()
    total_rejected = LoanRequest.objects.filter(status='Rejected').count()
    total_pending = LoanRequest.objects.filter(status='Pending').count()

    # Check unlocked loans (paid by this lender)
    unlocked_loans = set(
        Payment.objects.filter(lender=request.user, status="Completed").values_list("loan_request_id", flat=True)
    )

    # Add helper attribute to mark if unlocked
    for loan in all_loans:
        loan.is_paid = loan.id in unlocked_loans
    
   
    context = {
        "all_loans": all_loans,          # For complete list
        "pending_loans": pending_loans,  # Pending ones
        "total_today": total_today,
        "total_approved": total_approved,
        "total_rejected": total_rejected,
        "total_pending": total_pending,
    }

    return render(request, "dashboard_lender.html", context)

    

# -------------------- Dashboard Router --------------------
@login_required
def dashboard_router(request):
    role = getattr(request.user, "role", "applicant")
    if role == "lender":
        return redirect("dashboard_lender")
    return redirect("dashboard_applicant")


# -------------------- Reject Loan --------------------
@login_required
def reject_loan(request, loan_id):
    if request.method == "POST":
        reason = request.POST.get("reason", "").strip() or "No reason provided"

        # Loan object fetch karo
        loan = get_object_or_404(LoanRequest, id=loan_id)

        # Lender ke status record ko fetch ya create karo
        ls, created = LoanLenderStatus.objects.get_or_create(
            loan=loan,
            lender=request.user,
            defaults={"status": "Rejected", "remarks": reason, "deleted": False},
        )

        if not created:  # Agar pehle se exist karta hai to update karo
            ls.status = "Rejected"
            ls.remarks = reason
            ls.deleted = False  # safety
            ls.save()

        messages.error(request, f"Loan {loan.loan_id} rejected with reason: {reason}")

    return redirect("dashboard_lender")


# -------------------- Approve Loan (after payment) --------------------
@login_required
def approve_loan(request, loan_id):
    ls = get_object_or_404(LoanLenderStatus, loan_id=loan_id, lender=request.user)
    ls.status = "Approved"
    ls.remarks = "Payment done, Loan Approved"
    ls.save()
    messages.success(request, f"Loan {ls.loan.loan_id} approved successfully!")
    return redirect("dashboard_lender")

# -------------------- Loan Request --------------------
@login_required
def loan_request(request):
    """
    Applicant creates a loan request. Automatically assigns the request
    to all lenders by creating LoanLenderStatus entries.
    """
    if request.method == "POST":
        # Only applicants can create a loan request
        if getattr(request.user, "role", "") != "applicant":
            messages.error(request, "Only applicants can create loan requests.")
            return redirect("dashboard_router")

        # Create loan request
        loan = LoanRequest.objects.create(
            loan_id="LSH" + get_random_string(4, allowed_chars="0123456789"),
            applicant=request.user,
            loan_type=request.POST.get("loan_type") or "",
            amount_requested=request.POST.get("amount_requested") or 0,
            duration_months=request.POST.get("duration_months") or 0,
            interest_rate=request.POST.get("interest_rate") or 0,
            reason_for_loan=request.POST.get("reason") or None,
        )

        # Create LoanLenderStatus entries for ALL lenders
        lenders = User.objects.filter(role="lender")
        for lender in lenders:
            LoanLenderStatus.objects.create(
                loan=loan,
                lender=lender,
                status="Pending",
                remarks=loan.reason_for_loan or "Lender Reviewing Your Loan",
            )

        # Sync to Supabase (optional)
        try:
            from main.supabase_client import sync_loan_request_to_supabase
            sync_loan_request_to_supabase(loan)
        except Exception as e:
            print("❌ Supabase sync failed:", e)

        messages.success(request, "✅ Loan request submitted successfully.")
        return redirect("dashboard_router")

    return render(request, "loan_request.html")

# ✅ ---------------Reject Loan---------------
@login_required
def reject_loan(request, loan_id):
    if request.method == "POST":
        reason = request.POST.get("reason")
        ls = get_object_or_404(LoanLenderStatus, loan_id=loan_id, lender=request.user)
        ls.status = "Rejected"
        ls.remark = reason
        ls.save()
        messages.error(request, f"Loan {ls.loan.loan_id} rejected with reason: {reason}")
    return redirect("dashboard_lender")


# -------------------- Payment Page (Real Form Flow) --------------------
@login_required
def payment_page(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    if request.method == "POST":
        payment = Payment.objects.create(
            lender=request.user,
            loan_request=loan,
            payment_method=request.POST.get("payment_method"),
            amount=request.POST.get("amount"),
            status="Completed",
        )

        # ✅ Sync to Supabase
        try:
            sync_payment_to_supabase(payment)
        except Exception as e:
            print("Supabase payment sync failed:", e)

        # ✅ Update LoanLenderStatus
        ls = get_object_or_404(LoanLenderStatus, loan=loan, lender=request.user)
        ls.status = "Approved"
        ls.remark = "Payment done, Loan Approved"
        ls.save()

        messages.success(request, f"✅ Loan {loan.loan_id} approved after payment.")
        return redirect("dashboard_lender")

    return render(request, "payment.html", {"loan": loan})


# -------------------- Dummy Payment (Testing) --------------------
@login_required
def make_dummy_payment(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)

    # ✅ Dummy Payment create
    Payment.objects.create(
        loan_request=loan,
        lender=request.user,
        amount=loan.amount_requested,
        status="Completed",
        payment_method="Dummy"
    )

    # ✅ Update LoanLenderStatus
    ls = get_object_or_404(LoanLenderStatus, loan=loan, lender=request.user)
    ls.status = "Approved"
    ls.remark = "Dummy Payment done"
    ls.save()

    messages.success(request, f"✅ Dummy Payment done. Loan {loan.loan_id} marked as Approved.")
    return redirect("dashboard_lender")


# -------------------- View Profile (full)-----------
@login_required
def view_profile(request, user_id, loan_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()

    user = get_object_or_404(User, id=user_id)
    loan = get_object_or_404(LoanRequest, id=loan_id, applicant=user)

    # check karo ki payment done hai ya nahi
    has_payment = Payment.objects.filter(loan_request=loan, lender=request.user, status="Completed").exists()
    if not has_payment:
        messages.error(request, "You can only view applicant full profile after payment is done.")
        return redirect("dashboard_lender")

    return render(request, "view_profile.html", {
        "applicant": user,
        "loan": loan,
    })


# --------------View Profile (Partial)-----------
@login_required
def partial_profile(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    applicant = loan.applicant
    return render(request, "partial_profile.html", {
        "loan": loan,
        "applicant": applicant
    })

# -------------------- Forgot - Reset Password --------------------
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
