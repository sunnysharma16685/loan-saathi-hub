from flask import Flask, render_template, request, redirect, session, url_for
from supabase import create_client, Client
import random

app = Flask(__name__)
app.secret_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNva3h5bnlkZGJsb3VwZWRzem9qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mzg4NzA0MiwiZXhwIjoyMDY5NDYzMDQyfQ.qL4RdShkKKQRGfqYlfwjIwYmjRuYd5JG7LddIeLXkJg"

# Supabase config
SUPABASE_URL = "https://cokxynyddbloupedszoj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNva3h5bnlkZGJsb3VwZWRzem9qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4ODcwNDIsImV4cCI6MjA2OTQ2MzA0Mn0.gdeUkmoUs5qMW6vrzyOqRr0A1OVt_E_Tsq0nZ7X-h8A"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Helper: Custom ID Generator
def generate_custom_id(table, column, prefix):
    return f"{prefix}{random.randint(100000, 999999)}"

@app.route('/')
def home():
    return render_template('home.html', title="LoanSaathiHub – Trusted Loan Partner", description="Apply for loans easily and securely with LoanSaathiHub – Your trusted loan Saathi.")

@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form.get('last_name', '')
        mobile = request.form['mobile']
        email = request.form['email']

        user_id = generate_custom_id("users", "user_id", "LSHU")

        supabase.table("users").insert({
            "first_name": first_name,
            "last_name": last_name,
            "mobile": mobile,
            "email": email,
            "user_type": "loan_user",
            "user_id": user_id
        }).execute()

        session.update({'user': email, 'mobile': mobile, 'user_id': user_id})
        return redirect('/loan-request')

    return render_template('create_profile.html', title="Create Profile", description="Create your profile on LoanSaathiHub to apply for loans easily.")

@app.route('/loan-request', methods=['GET', 'POST'])
def loan_request():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        data = request.form
        loan_type = data['loan_type']
        short_code = "PL" if "personal" in loan_type.lower() else "HL" if "home" in loan_type.lower() else "LN"
        loan_id = generate_custom_id("loan_requests", "loan_id", short_code + "U")

        supabase.table("loan_requests").insert({
            "loan_id": loan_id,
            "user_email": session['user'],
            "loan_type": loan_type,
            "amount": data['amount'],
            "duration": data['duration'],
            "pincode": data['pincode'],
            "city": data['city'],
            "state": data['state'],
            "pan": data['pan'],
            "aadhar": data.get('aadhar'),
            "itr": data['itr'],
            "cibil": data.get('cibil'),
            "status": "In Process"
        }).execute()

        return render_template('thankyou.html', loan_id=loan_id)

    return render_template('loan_request.html', title="Loan Request", description="Submit your complete loan request on LoanSaathiHub.")


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    loans = supabase.table("loan_requests").select("*").eq("user_email", session['user']).order("applied_date", desc=True).execute().data
    return render_template('dashboard.html', loans=loans, user=session['user'], title="User Dashboard - LoanSaathiHub")

@app.route('/loan-approvals/<loan_id>')
def loan_approvals(loan_id):
    if 'user' not in session:
        return redirect('/login')

    approvals = supabase.table("loan_approvals").select("*").eq("loan_id", loan_id).execute().data
    for item in approvals:
        agent_info = supabase.table("agents").select("mobile").eq("email", item['agent_email']).single().execute()
        item['mobile'] = agent_info.data['mobile'] if agent_info.data else "N/A"

    return render_template('loan_approval_details.html', approvals=approvals, loan_id=loan_id, title="Loan Approvals")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form['login_id']
        res = supabase.table("users").select("*").or_(f"email.eq.{login_id},mobile.eq.{login_id}").execute()
        if res.data:
            session.update({'user': res.data[0]['email'], 'mobile': res.data[0]['mobile']})
            return redirect('/loan-request')  # ✅ Changed from /dashboard to /loan-request
        return render_template('login.html', error="Invalid login ID")

    return render_template('login.html', title="Login", description="Login to LoanSaathiHub using your email or mobile number.")


@app.route('/agent-signup', methods=['POST'])
def agent_signup():
    first_name = request.form['first_name']
    last_name = request.form.get('last_name', '')
    mobile = request.form['mobile']
    email = request.form['email']

    agent_id = generate_custom_id("agents", "agent_id", "LSHA")
    supabase.table("agents").insert({
        "first_name": first_name,
        "last_name": last_name,
        "mobile": mobile,
        "email": email,
        "status": "pending",
        "agent_stage": "basic_signup",
        "approved": False,
        "agent_id": agent_id
    }).execute()

    session.update({'agent': email, 'mobile': mobile, 'agent_id': agent_id})
    return redirect('/agent-profile')

@app.route('/agent-profile', methods=['GET', 'POST'])
def agent_profile():
    if 'agent' not in session:
        return redirect('/')

    if request.method == 'POST':
        data = request.form
        loan_types = data.getlist('loan_types')
        agent_mode = data.get('agent_mode')
        extra_fields = {}

        if agent_mode == 'proprietor':
            extra_fields = {
                "aadhar": data.get('proprietor_aadhar'),
                "agent_code": data.get('proprietor_code'),
                "bank": data.get('proprietor_bank')
            }
        elif agent_mode == 'bank':
            extra_fields = {
                "designation": data.get('bank_designation'),
                "branch": data.get('bank_branch'),
                "employee_id": data.get('bank_employee_id')
            }
        elif agent_mode == 'dsa':
            extra_fields = {
                "dsa_code": data.get('dsa_code'),
                "bank": data.get('dsa_bank')
            }

        supabase.table("agents").update({
            "loan_types": loan_types,
            "city": data.get('city'),
            "state": data.get('state'),
            "address": data.get('address'),
            "agent_mode": agent_mode,
            "status": "active",
            **extra_fields
        }).eq("email", session['agent']).execute()

        return redirect('/agent-dashboard')

    return render_template('agent_profile.html', title="Agent Profile")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Footer Pages
@app.route('/privacy')
def privacy(): return render_template('privacy.html')

@app.route('/about')
def about(): return render_template('about.html')

@app.route('/terms')
def terms(): return render_template('terms.html')

@app.route('/support')
def support(): return render_template('support.html')

@app.route('/contact')
def contact(): return render_template('contact.html')

@app.route('/forgot-password')
def forgot_password(): return "Coming soon..."

if __name__ == '__main__':
    app.run(debug=True)