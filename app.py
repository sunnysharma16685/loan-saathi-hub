from flask import Flask, render_template, request, redirect, session, url_for
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNva3h5bnlkZGJsb3VwZWRzem9qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mzg4NzA0MiwiZXhwIjoyMDY5NDYzMDQyfQ.qL4RdShkKKQRGfqYlfwjIwYmjRuYd5JG7LddIeLXkJg"

# Supabase Configuration
SUPABASE_URL = "https://cokxynyddbloupedszoj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNva3h5bnlkZGJsb3VwZWRzem9qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4ODcwNDIsImV4cCI6MjA2OTQ2MzA0Mn0.gdeUkmoUs5qMW6vrzyOqRr0A1OVt_E_Tsq0nZ7X-h8A"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------- Home -----------------------
@app.route('/')
def home():
    return render_template('home.html')


# ----------------------- Create Profile -----------------------
@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        # Basic Loan User profile data
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        mobile = request.form['mobile']
        email = request.form['email']

        # Save to Supabase
        supabase.table("users").insert({
            "first_name": first_name,
            "last_name": last_name,
            "mobile": mobile,
            "email": email,
            "user_type": "loan_user"
        }).execute()

        # Set session
        session['user'] = email
        session['mobile'] = mobile

        return redirect('/loan-request')
    return render_template('create_profile.html')

# ----------------------- Agent Profile-----------------
@app.route('/agent-signup', methods=['POST'])
def agent_signup():
    # Agent basic info
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    mobile = request.form['mobile']
    email = request.form['email']

    # Insert minimal agent data to track
    supabase.table("agents").insert({
        "first_name": first_name,
        "last_name": last_name,
        "mobile": mobile,
        "email": email,
        "status": "pending",
        "agent_stage": "basic_signup"
    }).execute()

    # Save session
    session['agent'] = email
    session['mobile'] = mobile

    # Redirect to full agent profile page
    return redirect('/agent-profile')

@app.route('/agent-profile', methods=['GET', 'POST'])
def agent_profile():
    if 'agent' not in session:
        return redirect('/')

    if request.method == 'POST':
        data = request.form

        # Get all loan type checkboxes
        loan_types = request.form.getlist('loan_types')
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

        # Save all data
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

    return render_template('agent_profile.html')


@app.route('/agent-dashboard', methods=['GET', 'POST'])
def agent_dashboard():
    if 'agent' not in session:
        return redirect('/')

    agent_email = session['agent']

    # Agent की details लो
    agent_data = supabase.table("agents").select("city").eq("email", agent_email).single().execute()
    agent_city = agent_data.data.get('city') if agent_data.data else None

    if not agent_city:
        return "Agent city not found. Please complete your profile."

    if request.method == 'POST':
        action = request.form.get('action')
        loan_id = request.form.get('loan_id')

        if action == 'reject':
            reason = request.form.get('reason')
            supabase.table("agent_leads").insert({
                "agent_email": agent_email,
                "loan_id": loan_id,
                "status": "rejected",
                "reason": reason
            }).execute()

        elif action == 'accept':
            # Simulate ₹99 payment done
            supabase.table("agent_leads").insert({
                "agent_email": agent_email,
                "loan_id": loan_id,
                "status": "accepted",
                "paid": True
            }).execute()

    # सभी loan_requests लो लेकिन सिर्फ उसी city के जहाँ agent है
    city_loans = supabase.table("loan_requests").select("*").eq("city", agent_city).execute().data

    # पहले से rejected या accepted leads हटाओ
    handled_ids = supabase.table("agent_leads").select("loan_id").eq("agent_email", agent_email).execute().data
    handled_loan_ids = [row['loan_id'] for row in handled_ids]

    unhandled_leads = [loan for loan in city_loans if loan['loan_id'] not in handled_loan_ids]

    return render_template("agent_dashboard.html", leads=unhandled_leads)

@app.route('/agent-dashboard')
def agent_dashboard():
    if 'agent' not in session:
        return redirect('/')

    # Agent approval check
    agent_email = session['agent']
    agent = supabase.table("agents").select("approved").eq("email", agent_email).single().execute()
    if not agent.data or not agent.data.get("approved"):
        return "Your account is pending approval by admin."

    # Proceed to dashboard...


@app.route('/agent-leads')
def agent_leads():
    if 'agent' not in session:
        return redirect('/')

    agent_email = session['agent']

    # Agent ने जो lead accept की हैं (paid=True)
    accepted_leads_data = supabase.table("agent_leads").select("loan_id").eq("agent_email", agent_email).eq("status", "accepted").eq("paid", True).execute()
    loan_ids = [entry['loan_id'] for entry in accepted_leads_data.data]

    # अब उन loan_ids की details लो
    all_leads = []
    for loan_id in loan_ids:
        loan_data = supabase.table("loan_requests").select("*").eq("loan_id", loan_id).single().execute()
        if loan_data.data:
            all_leads.append(loan_data.data)

    return render_template("agent_leads.html", leads=all_leads)
supabase.table("agents").insert({
    "full_name": data['first_name'] + " " + data['last_name'],
    "email": data['email'],
    "mobile": data['mobile'],
    "city": data['city'],
    "state": data['state'],
    "address": data['address'],
    "mode": data['mode'],
    "approved": False
}).execute()

# ----------------------- Admin Agent -----------------------
@app.route('/admin-agents', methods=['GET', 'POST'])
def admin_agents():
    if 'admin' not in session:
        return redirect('/admin-login')

    if request.method == 'POST':
        agent_email = request.form['email']
        action = request.form['action']

        if action == 'approve':
            supabase.table("agents").update({"approved": True}).eq("email", agent_email).execute()
        elif action == 'reject':
            supabase.table("agents").delete().eq("email", agent_email).execute()

    agents = supabase.table("agents").select("*").eq("approved", False).execute()
    return render_template("admin_agents.html", agents=agents.data)


# ----------------------- Loan Request -----------------------
@app.route('/loan-request', methods=['GET', 'POST'])
def loan_request():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        data = request.form

        # Generate new loan_id
        latest = supabase.table("loan_requests").select("loan_id").order("loan_id", desc=True).limit(1).execute()
        last_id = int(latest.data[0]['loan_id']) if latest.data else 19870000
        new_loan_id = str(last_id + 1)

        # Insert loan request
        supabase.table("loan_requests").insert({
            "loan_id": new_loan_id,
            "user_email": session['user'],
            "loan_type": data['loan_type'],
            "amount": data['amount'],
            "duration": data['duration'],
            "status": "In Process"
        }).execute()

        return render_template('thankyou.html', loan_id=new_loan_id)

    return render_template('loan_request.html')


# ----------------------- Login -----------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form['login_id']

        # Check by email or mobile
        res = supabase.table("users").select("*").or_(f"email.eq.{login_id},mobile.eq.{login_id}").execute()

        if res.data:
            session['user'] = res.data[0]['email']
            session['mobile'] = res.data[0]['mobile']
            return redirect('/dashboard')
        else:
            return "Invalid Login ID"
    return render_template('login.html')


# ----------------------- Dashboard -----------------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    # Fetch user loans
    res = supabase.table("loan_requests").select("*").eq("user_email", session['user']).execute()
    return render_template('dashboard.html', user=session['user'], loans=res.data)


# ----------------------- Logout -----------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ----------------------- Admin Login -----------------------
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        if email == "mayuri.luhar@gmail.com":
            session['admin'] = email
            return redirect('/admin-dashboard')
        else:
            return "Unauthorized Access"
    return render_template('admin_login.html')


# ----------------------- Admin Dashboard -----------------------
@app.route('/admin-dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin-login')

    if request.method == 'POST':
        loan_id = request.form['loan_id']
        status = request.form['status']
        remark = request.form['remark']

        # Update loan status
        supabase.table("loan_requests").update({
            "status": status,
            "remark": remark
        }).eq("loan_id", loan_id).execute()

    # Fetch all loan requests
    res = supabase.table("loan_requests").select("*").execute()
    return render_template('admin_dashboard.html', loans=res.data)


# ----------------------- Forgot Password (Placeholder) -----------------------
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    return "Coming soon..."

# ----------------------- Static Info Pages -----------------------

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/support')
def support():
    return render_template('support.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


# ----------------------- Run App -----------------------
if __name__ == '__main__':
    app.run(debug=True)
