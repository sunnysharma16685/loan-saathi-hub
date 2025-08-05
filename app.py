# app.py
from flask import Flask, render_template, request, redirect, session, url_for
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNva3h5bnlkZGJsb3VwZWRzem9qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Mzg4NzA0MiwiZXhwIjoyMDY5NDYzMDQyfQ.qL4RdShkKKQRGfqYlfwjIwYmjRuYd5JG7LddIeLXkJg"

# Supabase Configuration
SUPABASE_URL = "https://cokxynyddbloupedszoj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNva3h5bnlkZGJsb3VwZWRzem9qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4ODcwNDIsImV4cCI6MjA2OTQ2MzA0Mn0.gdeUkmoUs5qMW6vrzyOqRr0A1OVt_E_Tsq0nZ7X-h8A"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------------- All your routes below here -----------------------

@app.route('/')
def generate_custom_id(table, id_column, prefix, length=5):
    latest = supabase.table(table).select(id_column).order(id_column, desc=True).limit(1).execute()
    if latest.data:
        last_id = latest.data[0][id_column].replace(prefix, "")
        new_num = int(last_id) + 1
    else:
        new_num = 1
    return f"{prefix}{str(new_num).zfill(length)}"

def home():
    return render_template('home.html')

@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        mobile = request.form['mobile']
        email = request.form['email']

        # Generate custom user ID
        user_id = generate_custom_id("users", "user_id", "LSHU")

        supabase.table("users").insert({
            "first_name": first_name,
            "last_name": last_name,
            "mobile": mobile,
            "email": email,
            "user_type": "loan_user",
            "user_id": user_id
        }).execute()

        session['user'] = email
        session['mobile'] = mobile
        session['user_id'] = user_id

        return redirect('/loan-request')
    return render_template('create_profile.html')


@app.route('/loan-request', methods=['GET', 'POST'])
def loan_request():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        data = request.form

        loan_type = data['loan_type']  # eg. personal_loan
        short_code = "PL" if "personal" in loan_type.lower() else "HL" if "home" in loan_type.lower() else "LN"
        prefix = short_code + "U"

        loan_id = generate_custom_id("loan_requests", "loan_id", prefix)

        supabase.table("loan_requests").insert({
            "loan_id": loan_id,
            "user_email": session['user'],
            "loan_type": loan_type,
            "amount": data['amount'],
            "duration": data['duration'],
            "status": "In Process"
        }).execute()

        return render_template('thankyou.html', loan_id=loan_id)

    return render_template('loan_request.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    loans = supabase.table("loan_requests").select("*").eq("user_email", session['user']).execute().data

    return render_template('dashboard.html', loans=loans)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form['login_id']
        res = supabase.table("users").select("*").or_(f"email.eq.{login_id},mobile.eq.{login_id}").execute()
        if res.data:
            session['user'] = res.data[0]['email']
            session['mobile'] = res.data[0]['mobile']
            return redirect('/dashboard')
        return "Invalid Login ID"
    return render_template('login.html')

@app.route('/agent-signup', methods=['POST'])
def agent_signup():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    mobile = request.form['mobile']
    email = request.form['email']

    # Generate agent ID
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

    session['agent'] = email
    session['mobile'] = mobile
    session['agent_id'] = agent_id

    return redirect('/agent-profile')

@app.route('/loan-approvals/<loan_id>')
def loan_approvals(loan_id):
    if 'user' not in session:
        return redirect('/login')

    approvals = supabase.table("loan_approvals").select("*").eq("loan_id", loan_id).execute().data

    enriched_data = []
    for item in approvals:
        agent_info = supabase.table("agents").select("mobile").eq("email", item['agent_email']).single().execute()
        item['mobile'] = agent_info.data['mobile'] if agent_info.data else "N/A"
        enriched_data.append(item)

    return render_template('loan_approvals.html', approvals=enriched_data, loan_id=loan_id)


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

    return render_template('agent_profile.html')

@app.route('/agent-dashboard', methods=['GET', 'POST'])
def agent_dashboard():
    if 'agent' not in session:
        return redirect('/')

    agent_email = session['agent']
    agent = supabase.table("agents").select("approved", "city").eq("email", agent_email).single().execute()

    if not agent.data or not agent.data.get("approved"):
        return "Your account is pending approval by admin."

    agent_city = agent.data.get('city')
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
            supabase.table("agent_leads").insert({
                "agent_email": agent_email,
                "loan_id": loan_id,
                "status": "accepted",
                "paid": True
            }).execute()

    city_loans = supabase.table("loan_requests").select("*").eq("city", agent_city).execute().data
    handled = supabase.table("agent_leads").select("loan_id").eq("agent_email", agent_email).execute().data
    handled_ids = [row['loan_id'] for row in handled]
    unhandled_leads = [loan for loan in city_loans if loan['loan_id'] not in handled_ids]

    return render_template("agent_dashboard.html", leads=unhandled_leads)

@app.route('/agent-leads')
def agent_leads():
    if 'agent' not in session:
        return redirect('/')

    agent_email = session['agent']
    accepted = supabase.table("agent_leads").select("loan_id").eq("agent_email", agent_email).eq("status", "accepted").eq("paid", True).execute()
    loan_ids = [row['loan_id'] for row in accepted.data]

    all_leads = []
    for loan_id in loan_ids:
        data = supabase.table("loan_requests").select("*").eq("loan_id", loan_id).single().execute()
        if data.data:
            all_leads.append(data.data)

    return render_template("agent_leads.html", leads=all_leads)

@app.route('/admin-users', methods=['GET', 'POST'])
def admin_users():
    if 'admin' not in session:
        return redirect('/admin-login')

    if request.method == 'POST':
        email = request.form['email']
        action = request.form['action']
        remark = request.form.get('remark', '')

        if action == 'deactivate':
            supabase.table("users").update({
                "status": "inactive",
                "remarks": remark
            }).eq("email", email).execute()

        elif action == 'delete':
            supabase.table("users").delete().eq("email", email).execute()

    users = supabase.table("users").select("*").execute().data
    return render_template("admin_users.html", users=users)


@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        if email == "mayuri.luhar@gmail.com":
            session['admin'] = email
            return redirect('/admin-dashboard')
        return "Unauthorized Access"
    return render_template('admin_login.html')

@app.route('/admin-dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin-login')

    if request.method == 'POST':
        loan_id = request.form['loan_id']
        status = request.form['status']
        remark = request.form['remark']
        supabase.table("loan_requests").update({"status": status, "remark": remark}).eq("loan_id", loan_id).execute()

    res = supabase.table("loan_requests").select("*").execute()
    return render_template('admin_dashboard.html', loans=res.data)

@app.route('/admin-agents', methods=['GET', 'POST'])
def admin_agents():
    if 'admin' not in session:
        return redirect('/admin-login')

    if request.method == 'POST':
        email = request.form['email']
        action = request.form['action']
        remark = request.form.get('remark', '')

        if action == 'approve':
            supabase.table("agents").update({
                "approved": True,
                "status": "active",
                "remarks": "Approved by Admin"
            }).eq("email", email).execute()

        elif action == 'reject':
            supabase.table("agents").delete().eq("email", email).execute()

        elif action == 'deactivate':
            supabase.table("agents").update({
                "status": "inactive",
                "remarks": remark
            }).eq("email", email).execute()

    pending_agents = supabase.table("agents").select("*").eq("approved", False).execute().data
    active_agents = supabase.table("agents").select("*").eq("approved", True).execute().data
    return render_template("admin_agents.html", pending_agents=pending_agents, active_agents=active_agents)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ----------------- Static Info Pages -----------------
@app.route('/about')
def about(): return render_template('about.html')

@app.route('/privacy')
def privacy(): return render_template('privacy.html')

@app.route('/terms')
def terms(): return render_template('terms.html')

@app.route('/support')
def support(): return render_template('support.html')

@app.route('/contact')
def contact(): return render_template('contact.html')

@app.route('/forgot-password')
def forgot_password():
    return "Coming soon..."

# ----------------- Run the app -----------------
if __name__ == '__main__':
    app.run(debug=True)
