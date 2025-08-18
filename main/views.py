from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import LoanRequest, Payment, UserProfile, AgentProfile, User
from django.utils.crypto import get_random_string
from django.db.models import Count, Q
from .supabase_client import supabase   # ✅ single source of truth

# 🟩 minor imports for safety
from django.utils.timezone import now


def index(request):
    return render(request, 'index.html')


# ------------------------
# Helper: profile complete?
# ------------------------
def is_profile_complete(user):
    """
    Priority:
    1) If custom field 'is_profile_complete' exists → use it
    2) Else infer by related profile minimal fields
    """
    try:
        if hasattr(user, "is_profile_complete"):
            return bool(getattr(user, "is_profile_complete"))
    except Exception:
        pass

    role = getattr(user, "role", "")
    if role == "user":
        try:
            p = user.userprofile
            return bool(p.first_name and p.mobile)
        except Exception:
            return False
    if role == "agent":
        try:
            p = user.agentprofile
            return bool(p.first_name and p.mobile)
        except Exception:
            return False
    if role == "admin":
        return True
    return False


def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user_type = request.POST.get("user_type")  # user/agent

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)

            # ✅ robust profile-complete check
            if not is_profile_complete(user):
                if user.role == "user":
                    return redirect("complete_profile_user")
                elif user.role == "agent":
                    return redirect("complete_profile_agent")
                elif user.role == "admin":
                    return redirect("complete_profile_admin")

            # profile complete hai → direct dashboard
            if user.role == "user":
                return redirect("dashboard_user")
            elif user.role == "agent":
                return redirect("dashboard_agent")
            elif user.role == "admin":
                return redirect("dashboard_admin")

        else:
            messages.error(request, "गलत ईमेल या पासवर्ड")
    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect('index')


@login_required
def dashboard_user(request):
    loans = LoanRequest.objects.filter(user=request.user)
    return render(request, 'dashboard_user.html', {'loans': loans})


@login_required
def dashboard_agent(request):
    loans = LoanRequest.objects.all()
    return render(request, 'dashboard_agent.html', {'loans': loans})


@login_required
def loan_request(request):
    if request.method == 'POST':
        loan_type = request.POST.get('loan_type')
        amount_requested = request.POST.get('amount_requested')
        duration_months = request.POST.get('duration_months')
        interest_rate = request.POST.get('interest_rate')
        remarks = request.POST.get('remarks')

        loan_id = "LSH" + get_random_string(4, allowed_chars='0123456789')
        LoanRequest.objects.create(
            loan_id=loan_id,
            user=request.user,
            loan_type=loan_type,
            amount_requested=amount_requested,
            duration_months=duration_months,
            interest_rate=interest_rate,
            remarks=remarks
        )
        return redirect('dashboard_user')

    return render(request, 'loan_request.html')


@login_required
def payment_page(request, loan_id):
    loan = get_object_or_404(LoanRequest, id=loan_id)
    if request.method == 'POST':
        Payment.objects.create(
            agent=request.user,
            loan_request=loan,
            payment_method=request.POST.get('payment_method'),
            amount=request.POST.get('amount'),
            status='done'
        )
        return redirect('dashboard_agent')

    return render(request, 'payment.html', {'loan': loan})


# ------------------------
# PROFILE VIEWS
# ------------------------

def complete_profile_user(request):
    if request.method == "POST":
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")

        # पहले से मौजूद user check करो
        if User.objects.filter(email=email).exists() or User.objects.filter(mobile=mobile).exists():
            messages.error(request, "Your mobile or email is already registered with us")
            return redirect("complete_profile_user")  # वही form पर वापस भेज दो

        # नया profile create करो
        # OLD FIELDS (preserved)
        if 'full_name' in request.POST: profile.full_name = request.POST.get('full_name')
        if 'dob' in request.POST: profile.dob = request.POST.get('dob')
        if 'gender' in request.POST: profile.gender = request.POST.get('gender')
        if 'marital_status' in request.POST: profile.marital_status = request.POST.get('marital_status')
        if 'nationality' in request.POST: profile.nationality = request.POST.get('nationality')
        if 'pan_number' in request.POST or 'pan' in request.POST:
            # 🟩 avoid duplicate assignment
            profile.pan_number = request.POST.get('pan_number') or request.POST.get('pan')
        if 'voter_id' in request.POST: profile.voter_id = request.POST.get('voter_id')
        if 'bank_account_no' in request.POST: profile.bank_account_no = request.POST.get('bank_account_no')
        if 'ifsc_code' in request.POST: profile.ifsc_code = request.POST.get('ifsc_code')
        if 'reason_for_loan' in request.POST: profile.reason_for_loan = request.POST.get('reason_for_loan')

        # NEW FIELDS (stepper form)
        if 'title' in request.POST: profile.title = request.POST.get('title')
        if 'firstName' in request.POST: profile.first_name = request.POST.get('firstName')
        if 'lastName' in request.POST: profile.last_name = request.POST.get('lastName')
        if 'mobile' in request.POST: profile.mobile = request.POST.get('mobile')
        if 'email' in request.POST: profile.email = request.POST.get('email')
        if 'password_hash' in request.POST: profile.password_hash = request.POST.get('password_hash')
        if 'address' in request.POST: profile.address = request.POST.get('address')
        if 'pincode' in request.POST: profile.pincode = request.POST.get('pincode')
        if 'city' in request.POST: profile.city = request.POST.get('city')
        if 'state' in request.POST: profile.state = request.POST.get('state')
        if 'aadhaar' in request.POST: profile.aadhaar = request.POST.get('aadhaar')
        if 'itr' in request.POST: profile.itr = request.POST.get('itr')
        if 'cibil' in request.POST: profile.cibil = request.POST.get('cibil')

        # Job
        if 'type' in request.POST: profile.work_type = request.POST.get('type')
        if 'jobType' in request.POST: profile.job_type = request.POST.get('jobType')
        if 'employmentType' in request.POST: profile.employment_type = request.POST.get('employmentType')
        if 'companyName' in request.POST: profile.company_name = request.POST.get('companyName')
        if 'jobDesignation' in request.POST: profile.job_designation = request.POST.get('jobDesignation')
        if 'totalExperience' in request.POST: profile.total_experience = request.POST.get('totalExperience')
        if 'currentExperience' in request.POST: profile.current_experience = request.POST.get('currentExperience')
        if 'salaryMode' in request.POST: profile.salary_mode = request.POST.get('salaryMode')
        if 'monthlySalary' in request.POST: profile.monthly_salary = request.POST.get('monthlySalary')
        if 'otherIncome' in request.POST: profile.other_income = request.POST.get('otherIncome')

        # Business
        if 'businessTurnover' in request.POST: profile.business_turnover = request.POST.get('businessTurnover')
        if 'businessDesignation' in request.POST: profile.business_designation = request.POST.get('businessDesignation')

        profile.save()

        # ✅ also mirror basics to User & mark complete when field exists
        try:
            u = request.user
            if getattr(u, "first_name", None) is not None and profile.first_name:
                u.first_name = profile.first_name
            if getattr(u, "last_name", None) is not None and profile.last_name:
                u.last_name = profile.last_name
            if getattr(u, "email", None) is not None and profile.email:
                u.email = profile.email
            if getattr(u, "role", None) is not None:
                u.role = "user"
            if hasattr(u, "is_profile_complete"):
                u.is_profile_complete = True
            u.save()
        except Exception:
            pass

        # --- sync with Supabase ---
        data_user = {
            "id": str(request.user.id),
            "username": request.user.username,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "email": profile.email,
            "mobile": profile.mobile,
            "password_hash": getattr(profile, "password_hash", "NA"),
            "role": "user",
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
            "date_joined": "now()",  # keep same behavior
        }
        try:
            supabase.table("users").upsert(data_user).execute()
        except Exception as e:
            print("Supabase sync error (user->users):", e)

        data_profile = {
            "id": str(request.user.id),
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "email": profile.email,
            "mobile": profile.mobile,
            "role": "user",
            "custom_id": f"U{request.user.id}"
        }
        try:
            supabase.table("user_profiles").upsert(data_profile).execute()
        except Exception as e:
            print("Supabase sync error (user->user_profiles):", e)

        messages.success(request, "Profile created successfully")
        return redirect('dashboard_user')

    return render(request, "complete_profile_user.html")


def complete_profile_agent(request):
    if request.method == "POST":
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")

        # पहले से मौजूद agent check करो
        if User.objects.filter(email=email).exists() or User.objects.filter(mobile=mobile).exists():
            messages.error(request, "Your mobile or email is already registered with us")
            return redirect("complete_profile_agent")

        # नया profile create करो
        # Basic
        profile.title = request.POST.get('title')
        profile.first_name = request.POST.get('firstName')
        profile.last_name = request.POST.get('lastName')
        profile.mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        if email:
            profile.email = email
        profile.password_hash = request.POST.get('password_hash')

        # Personal
        profile.dob = request.POST.get('dob')
        profile.gender = request.POST.get('gender')
        profile.address = request.POST.get('address')
        profile.pincode = request.POST.get('pincode')
        profile.city = request.POST.get('city')
        profile.state = request.POST.get('state')
        profile.pan_number = request.POST.get('pan')

        # Business
        profile.business_type = request.POST.get('businessType')
        profile.gst_no = request.POST.get('gstNo')
        profile.dsa_code = request.POST.get('dsaCode')
        profile.business_name = request.POST.get('businessName')
        profile.designation = request.POST.get('businessDesignation')
        profile.turnover = request.POST.get('businessTurnover')

        profile.save()

        # ✅ mirror basics to User & mark complete if field exists
        try:
            u = request.user
            if getattr(u, "first_name", None) is not None and profile.first_name:
                u.first_name = profile.first_name
            if getattr(u, "last_name", None) is not None and profile.last_name:
                u.last_name = profile.last_name
            if getattr(u, "email", None) is not None and profile.email:
                u.email = profile.email
            if getattr(u, "role", None) is not None:
                u.role = "agent"
            if hasattr(u, "is_profile_complete"):
                u.is_profile_complete = True
            u.save()
        except Exception:
            pass

        # --- sync with Supabase ---
        data_user = {
            "id": str(request.user.id),
            "username": request.user.username,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "email": profile.email,
            "mobile": profile.mobile,
            "password_hash": getattr(profile, "password_hash", "NA"),
            "role": "agent",
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
            "date_joined": "now()",
        }
        try:
            supabase.table("users").upsert(data_user).execute()
        except Exception as e:
            print("Supabase sync error (agent->users):", e)

        data_agent = {
            "id": str(request.user.id),
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "email": profile.email,
            "mobile": profile.mobile,
            "role": "agent",
            "custom_id": f"A{request.user.id}"
        }
        try:
            supabase.table("agent_profiles").upsert(data_agent).execute()
        except Exception as e:
            print("Supabase sync error (agent->agent_profiles):", e)
         
        messages.success(request, "Profile created successfully")
        return redirect('dashboard_agent')

    return render(request, "complete_profile_user.html")


# ------------------------
# COMPLETE ADMIN PROFILE
# ------------------------
@login_required
def complete_profile_admin(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')

        # --- update local user ---
        user = request.user
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.mobile = mobile
        user.role = "admin"
        user.is_staff = True
        user.is_superuser = True
        if hasattr(user, "is_profile_complete"):
            user.is_profile_complete = True
        user.save()

        # --- sync with Supabase ---
        try:
            supabase.table("users").upsert({
                "id": str(user.id),
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "mobile": mobile,
                "role": "admin",
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
            }).execute()
        except Exception as e:
            print("Supabase sync error (admin profile):", e)

        return redirect('dashboard_admin')

    return render(request, 'complete_profile_admin.html')


# ------------------------
# ADMIN LOGIN
# ------------------------
def admin_login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")  # email or mobile
        password = request.POST.get("password")

        user = authenticate(request, username=identifier, password=password)

        if user is not None and user.role == "admin":
            login(request, user)
            return redirect("dashboard_admin")
        else:
            messages.error(request, "Invalid admin credentials or unauthorized access.")

    return render(request, "admin_login.html")


# ------------------------
# ADMIN DASHBOARD
# ------------------------
@login_required
def dashboard_admin(request):
    if request.user.role != "admin":
        messages.error(request, "Access denied. Admins only.")
        return redirect("index")

    try:
        # Local DB fetch
        users = UserProfile.objects.all()
        agents = AgentProfile.objects.all()
        payments = Payment.objects.all()
        loans = LoanRequest.objects.all()

        # --- Sync snapshot to Supabase ---
        try:
            supabase.table("user_profiles").upsert([
                {
                    "id": str(u.id),
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                    "email": u.email,
                    "mobile": u.mobile,
                    "role": "user"
                } for u in users
            ]).execute()

            supabase.table("agent_profiles").upsert([
                {
                    "id": str(a.id),
                    "first_name": a.first_name,
                    "last_name": a.last_name,
                    "email": a.email,
                    "mobile": a.mobile,
                    "role": "agent"
                } for a in agents
            ]).execute()

            supabase.table("payments").upsert([
                {
                    "id": str(p.id),
                    "loan_id": str(p.loan_request.id),
                    "agent_id": str(p.agent.id),
                    "amount": p.amount,
                    "status": p.status
                } for p in payments
            ]).execute()

            supabase.table("loan_requests").upsert([
                {
                    "id": str(l.id),
                    "loan_id": l.loan_id,
                    "loan_type": l.loan_type,
                    "amount": l.amount_requested,
                    "status": l.status
                } for l in loans
            ]).execute()

        except Exception as e:
            print("Supabase sync error (admin dashboard):", e)

    except Exception as e:
        print("DB fetch error (admin dashboard):", e)
        users, agents, payments, loans = [], [], [], []

    return render(request, "admin_dashboard.html", {
        "users": users,
        "agents": agents,
        "payments": payments,
        "loans": loans,
    })
