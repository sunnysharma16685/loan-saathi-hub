from flask import Flask, render_template, request, redirect, session, url_for
from supabase import create_client, Client
import random

app = Flask(__name__)
app.secret_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkbmJhc3h5eXllcXB4dHBycGF2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NDU0NTQ2NSwiZXhwIjoyMDcwMTIxNDY1fQ.hRDZg4frXsGW5E5jAv80ctXz75yCI_lJDfaNllGKJcQ"

# Supabase config
SUPABASE_URL = "https://vdnbasxyyyeqpxtprpav.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkbmJhc3h5eXllcXB4dHBycGF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ1NDU0NjUsImV4cCI6MjA3MDEyMTQ2NX0.1VmiedWObblpLWgoaIi60KBUOnMfJYrqhU15_9BU_Ps"

# Helper: Custom ID Generator
def generate_custom_id(table, column, prefix):
    return f"{prefix}{random.randint(100000, 999999)}"

@app.route('/')
def home():
    return redirect(url_for('login'))
    return render_template('home.html', title="LoanSaathiHub – Trusted Loan Partner", description="Apply for loans easily and securely with LoanSaathiHub – Your trusted loan Saathi.")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        title = request.form['title']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        mobile = request.form['mobile']
        email = request.form['email']
        password = request.form['password']
        repeat_password = request.form['repeat_password']
	
	if email in users:
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('login'))

        if password != repeat_password:
            flash('Passwords do not match. Try again.', 'danger')
            return render_template('create_profile.html')

        # Custom user ID generator
        user_id = generate_custom_id("users", "user_id", "LSHU")

        # Optional: check if user already exists
        existing_user = supabase.table("users").select("*").eq("email", email).execute()

        if existing_user.data:
            session["user"] = existing_user.data[0]
        else:
            response = supabase.table("users").insert({
                "title": title,
                "first_name": first_name,
                "last_name": last_name,
                "mobile": mobile,
                "email": email,
                "user_type": "loan_user",
                "user_id": user_id
            }).execute()

            session.update({
                'user': email,
                'mobile': mobile,
                'user_id': user_id
            })

        return redirect("/loan_request")

    return render_template("login.html", title="LoanSaathiHub – Login", description="Create or log in to your profile.")


@app.route('/loan_request', methods=['GET', 'POST'])
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
	return redirect("/dashboard")

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
@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email_or_mobile = request.form['email_or_mobile']

        # Add your password recovery logic here (send OTP/email link)
        # Placeholder: pretend success
        message = "Password reset link has been sent to your email or mobile."
        return render_template('forgot.html', message=message)

    return render_template('forgot.html')


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