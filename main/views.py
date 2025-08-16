from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import LoanRequest, Payment, UserProfile, AgentProfile, User
from django.utils.crypto import get_random_string

def index(request):
    return render(request, 'index.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.role == role:
            login(request, user)
            if role == 'user':
                return redirect('dashboard_user')
            elif role == 'agent':
                return redirect('dashboard_agent')
        else:
            messages.error(request, "Invalid credentials or role.")
    return render(request, 'login.html')


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


@login_required
def complete_profile_user(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name')
        profile.dob = request.POST.get('dob')
        profile.gender = request.POST.get('gender')
        profile.marital_status = request.POST.get('marital_status')
        profile.nationality = request.POST.get('nationality')
        profile.pan_number = request.POST.get('pan_number')
        profile.voter_id = request.POST.get('voter_id')
        profile.passport_no = request.POST.get('passport_no')
        profile.driving_license = request.POST.get('driving_license')
        profile.bank_account_no = request.POST.get('bank_account_no')
        profile.ifsc_code = request.POST.get('ifsc_code')
        profile.reason_for_loan = request.POST.get('reason_for_loan')
        profile.occupation = request.POST.get('occupation')
        profile.company_name = request.POST.get('company_name')
        profile.designation = request.POST.get('designation')
        profile.turnover = request.POST.get('turnover')
        profile.save()
        return redirect('dashboard_user')

    return render(request, 'complete_profile_user.html', {'profile': profile})


@login_required
def complete_profile_agent(request):
    profile, created = AgentProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name')
        profile.dob = request.POST.get('dob')
        profile.gender = request.POST.get('gender')
        profile.marital_status = request.POST.get('marital_status')
        profile.nationality = request.POST.get('nationality')
        profile.pan_number = request.POST.get('pan_number')
        profile.voter_id = request.POST.get('voter_id')
        profile.passport_no = request.POST.get('passport_no')
        profile.driving_license = request.POST.get('driving_license')
        profile.bank_account_no = request.POST.get('bank_account_no')
        profile.ifsc_code = request.POST.get('ifsc_code')
        profile.business_type = request.POST.get('business_type')
        profile.gst_no = request.POST.get('gst_no')
        profile.dsa_code_name = request.POST.get('dsa_code_name')
        profile.business_name = request.POST.get('business_name')
        profile.designation = request.POST.get('designation')
        profile.turnover = request.POST.get('turnover')
        profile.save()
        return redirect('dashboard_agent')

    return render(request, 'complete_profile_agent.html', {'profile': profile})
