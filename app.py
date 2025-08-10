import os
from supabase import create_client

SUPABASE_URL = os.getenv("https://vdnbasxyyyeqpxtprpav.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZkbmJhc3h5eXllcXB4dHBycGF2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ1NDU0NjUsImV4cCI6MjA3MDEyMTQ2NX0.1VmiedWObblpLWgoaIi60KBUOnMfJYrqhU15_9BU_Ps")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

from flask import Flask, render_template

app = Flask(__name__)

# === Routes ===

@app.route('/')
def homepage():
    # by default show index; you may choose to redirect to login
    return render_template('index.html')

# === Simple in-memory mock DB (still useful for quick registration flow) ===
USERS = {}
AGENTS = {}

# Static Pincode mapping (demo)
PINCODE_DATA = {
    "110001": {"city": "New Delhi", "state": "Delhi"},
    "560001": {"city": "Bengaluru", "state": "Karnataka"},
    "400001": {"city": "Mumbai", "state": "Maharashtra"},
    # add more as needed
}

# Make pincodes available to templates (for JS auto-fill)
@app.context_processor
def inject_common_data():
    return dict(pincode_data=PINCODE_DATA)

# === Helpers ===
def generate_custom_id(table, column, prefix):
    """Generate a simple random custom id (prefix + 6 digits)."""
    return f"{prefix}{random.randint(100000, 999999)}"

def validate_pin_city_state(pincode, city, state):
    valid = PINCODE_DATA.get(pincode)
    if not valid:
        return False
    return valid['city'].lower() == city.lower() and valid['state'].lower() == state.lower()



# ---------- Unified Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form.get('user_id', '').strip() or request.form.get('login_id', '').strip()
        # 1) Check local USERS/AGENTS by mobile (we used mobile as user_id)
        if login_id:
            if login_id in USERS:
                user = USERS[login_id]
                session['user_id'] = login_id
                session['role'] = 'user'
                session['first_name'] = user.get('first_name')
                flash("Login successful (local user).", "success")
                return redirect(url_for('dashboard_user'))
            if login_id in AGENTS:
                agent = AGENTS[login_id]
                session['user_id'] = login_id
                session['role'] = 'agent'
                session['first_name'] = agent.get('first_name')
                flash("Login successful (local agent).", "success")
                return redirect(url_for('dashboard_agent'))

        # 2) Fallback: check Supabase users table by email or mobile
        if login_id:
            try:
                res = supabase.table("users").select("*").or_(f"email.eq.{login_id},mobile.eq.{login_id}").execute()
                if res and res.data:
                    u = res.data[0]
                    session.update({'user': u.get('email'), 'mobile': u.get('mobile')})
                    flash("Login successful (Supabase).", "success")
                    return redirect(url_for('dashboard_supabase'))
            except Exception as e:
                app.logger.error("Supabase login error: %s", e)

        flash("Invalid credentials or user not registered.", "error")

    return render_template('login.html')

# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for('homepage'))

# ---------- Register (local quick registration) ----------
@app.route('/register/<role>', methods=['POST'])
def register(role):
    title = request.form.get('title')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    mobile = request.form.get('mobile')
    email = request.form.get('email')

    if not all([title, first_name, last_name, mobile, email]):
        flash("Please fill all fields", "error")
        return redirect(url_for('homepage'))

    user_id = mobile

    # Check duplicates in local stores or Supabase
    if user_id in USERS or user_id in AGENTS:
        flash("User already registered locally. Please login.", "error")
        return redirect(url_for('login'))

    # optional: check supabase for same mobile/email
    try:
        sup_res = supabase.table("users").select("*").or_(f"email.eq.{email},mobile.eq.{mobile}").execute()
        if sup_res and sup_res.data:
            flash("User already registered in main DB. Please login.", "error")
            return redirect(url_for('login'))
    except Exception:
        pass  # ignore supabase errors for local flow

    # Save temp reg_data to session
    session['reg_data'] = {
        "user_id": user_id,
        "title": title,
        "first_name": first_name,
        "last_name": last_name,
        "mobile": mobile,
        "email": email,
        "role": role,
    }

    # redirect to appropriate completion form
    if role == 'user':
        return redirect(url_for('complete_profile_user'))
    else:
        return redirect(url_for('complete_profile_agent'))

# ---------- Complete Profile: User (local) ----------
@app.route('/complete-profile/user', methods=['GET', 'POST'])
def complete_profile_user():
    reg_data = session.get('reg_data')
    if not reg_data or reg_data.get('role') != 'user':
        flash("No registration data found. Please register first.", "error")
        return redirect(url_for('homepage'))

    if request.method == 'POST':
        loan_type = request.form.get('loan_type')
        amount = request.form.get('amount')
        duration = request.form.get('duration')
        pincode = request.form.get('pincode')
        city = request.form.get('city')
        state = request.form.get('state')
        pan = request.form.get('pan')
        aadhar = request.form.get('aadhar')
        itr = request.form.get('itr')
        cibil = request.form.get('cibil')

        if not all([loan_type, amount, duration, pincode, city, state, pan, itr]):
            flash("Please fill all mandatory fields", "error")
            return redirect(url_for('complete_profile_user'))

        if not validate_pin_city_state(pincode, city, state):
            flash("City or State does not match the provided PIN Code.", "error")
            return redirect(url_for('complete_profile_user'))

        user_id = reg_data['user_id']
        USERS[user_id] = {
            **reg_data,
            "loan_type": loan_type,
            "amount": amount,
            "duration": duration,
            "pincode": pincode,
            "city": city,
            "state": state,
            "pan": pan,
            "aadhar": aadhar,
            "itr": itr,
            "cibil": cibil,
        }
        session['user_id'] = user_id
        session['role'] = 'user'
        session['first_name'] = reg_data['first_name']
        session.pop('reg_data', None)
        flash("Profile completed successfully (local)!", "success")
        return redirect(url_for('dashboard_user'))

    return render_template('complete_profile_user.html', user=reg_data)

# ---------- Complete Profile: Agent (local) ----------
@app.route('/complete-profile/agent', methods=['GET', 'POST'])
def complete_profile_agent():
    reg_data = session.get('reg_data')
    if not reg_data or reg_data.get('role') != 'agent':
        flash("No registration data found. Please register first.", "error")
        return redirect(url_for('homepage'))

    if request.method == 'POST':
        loan_type = request.form.get('loan_type')
        amount = request.form.get('amount')
        duration = request.form.get('duration')
        pincode = request.form.get('pincode')
        city = request.form.get('city')
        state = request.form.get('state')
        pan = request.form.get('pan')
        aadhar = request.form.get('aadhar')
        itr = request.form.get('itr')
        cibil = request.form.get('cibil')

        agent_type = request.form.get('agent_type')
        firm_name = request.form.get('firm_name')
        firm_code = request.form.get('firm_code')
        bank_name = request.form.get('bank_name')

        if not all([loan_type, amount, duration, pincode, city, state, pan, itr, agent_type, firm_name, firm_code, bank_name]):
            flash("Please fill all mandatory fields", "error")
            return redirect(url_for('complete_profile_agent'))

        if not validate_pin_city_state(pincode, city, state):
            flash("City or State does not match the provided PIN Code.", "error")
            return redirect(url_for('complete_profile_agent'))

        user_id = reg_data['user_id']
        AGENTS[user_id] = {
            **reg_data,
            "loan_type": loan_type,
            "amount": amount,
            "duration": duration,
            "pincode": pincode,
            "city": city,
            "state": state,
            "pan": pan,
            "aadhar": aadhar,
            "itr": itr,
            "cibil": cibil,
            "agent_type": agent_type,
            "firm_name": firm_name,
            "firm_code": firm_code,
            "bank_name": bank_name,
        }
        session['user_id'] = user_id
        session['role'] = 'agent'
        session['first_name'] = reg_data['first_name']
        session.pop('reg_data', None)
        flash("Agent profile completed successfully (local)!", "success")
        return redirect(url_for('dashboard_agent'))

    return render_template('complete_profile_agent.html', user=reg_data)

# ---------- Local Dashboards ----------
@app.route('/dashboard/user')
def dashboard_user():
    if session.get('role') != 'user' or 'user_id' not in session:
        flash("Please login to access user dashboard", "error")
        return redirect(url_for('login'))
    first_name = session.get('first_name')
    user_id = session.get('user_id')
    profile = USERS.get(user_id)
    return render_template('dashboard_user.html', first_name=first_name, profile=profile)

@app.route('/dashboard/agent')
def dashboard_agent():
    if session.get('role') != 'agent' or 'user_id' not in session:
        flash("Please login to access agent dashboard", "error")
        return redirect(url_for('login'))
    first_name = session.get('first_name')
    agent_id = session.get('user_id')
    profile = AGENTS.get(agent_id)
    return render_template('dashboard_agent.html', first_name=first_name, profile=profile)

# ---------- Supabase-backed flows (persistent) ----------
@app.route('/loan_request', methods=['GET', 'POST'])
def loan_request():
    # require supabase session user OR local user mapped to an email
    if 'user' not in session and 'user_id' not in session:
        flash("Please login to submit a loan request.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.form
        loan_type = data.get('loan_type', '')
        short_code = "PL" if "personal" in loan_type.lower() else "HL" if "home" in loan_type.lower() else "LN"
        loan_id = generate_custom_id("loan_requests", "loan_id", short_code + "U")

        payload = {
            "loan_id": loan_id,
            "user_email": session.get('user') or session.get('user_id') + "@local",
            "loan_type": loan_type,
            "amount": data.get('amount'),
            "duration": data.get('duration'),
            "pincode": data.get('pincode'),
            "city": data.get('city'),
            "state": data.get('state'),
            "pan": data.get('pan'),
            "aadhar": data.get('aadhar'),
            "itr": data.get('itr'),
            "cibil": data.get('cibil'),
            "status": "In Process"
        }

        try:
            supabase.table("loan_requests").insert(payload).execute()
            return render_template('thankyou.html', loan_id=loan_id)
        except Exception as e:
            app.logger.error("Error inserting loan_request: %s", e)
            flash("There was an error submitting your request. Please try again later.", "error")
            return redirect(url_for('loan_request'))

    return render_template('loan_request.html')

@app.route('/dashboard/supabase')
def dashboard_supabase():
    if 'user' not in session:
        flash("Please login first.", "error")
        return redirect(url_for('login'))
    try:
        loans_res = supabase.table("loan_requests").select("*").eq("user_email", session['user']).order("applied_date", desc=True).execute()
        loans = loans_res.data if loans_res and loans_res.data else []
    except Exception as e:
        app.logger.error("Supabase fetch error: %s", e)
        loans = []
    return render_template('dashboard.html', loans=loans, user=session.get('user'))

@app.route('/loan-approvals/<loan_id>')
def loan_approvals(loan_id):
    if 'user' not in session:
        flash("Please login first.", "error")
        return redirect(url_for('login'))
    try:
        approvals_res = supabase.table("loan_approvals").select("*").eq("loan_id", loan_id).execute()
        approvals = approvals_res.data if approvals_res and approvals_res.data else []
        for item in approvals:
            agent_info = supabase.table("agents").select("mobile").eq("email", item.get('agent_email')).single().execute()
            item['mobile'] = agent_info.data.get('mobile') if agent_info and agent_info.data else "N/A"
    except Exception as e:
        app.logger.error("Error fetching approvals: %s", e)
        approvals = []
    return render_template('loan_approval_details.html', approvals=approvals, loan_id=loan_id)

# Supabase agent signup & profile
@app.route('/agent-signup', methods=['POST'])
def agent_signup():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name', '')
    mobile = request.form.get('mobile')
    email = request.form.get('email')

    agent_id = generate_custom_id("agents", "agent_id", "LSHA")
    try:
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
        return redirect(url_for('agent_profile'))
    except Exception as e:
        app.logger.error("Agent signup error: %s", e)
        flash("Error signing up agent. Try later.", "error")
        return redirect(url_for('homepage'))

@app.route('/agent-profile', methods=['GET', 'POST'])
def agent_profile():
    if 'agent' not in session:
        flash("Please complete signup first.", "error")
        return redirect(url_for('homepage'))

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

        update_payload = {
            "loan_types": loan_types,
            "city": data.get('city'),
            "state": data.get('state'),
            "address": data.get('address'),
            "agent_mode": agent_mode,
            "status": "active",
            **extra_fields
        }

        try:
            supabase.table("agents").update(update_payload).eq("email", session['agent']).execute()
            return redirect('/agent-dashboard')
        except Exception as e:
            app.logger.error("Error updating agent profile: %s", e)
            flash("Error updating profile. Try later.", "error")
            return redirect(url_for('agent_profile'))

    return render_template('agent_profile.html')

# ---------- Misc pages ----------
@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # simple placeholder behaviour
        email_or_mobile = request.form.get('email_or_mobile')
        message = "Password reset link has been sent to your email or mobile."
        return render_template('forgot.html', message=message)
    return render_template('forgot.html')

# Footer static pages (use same templates as in base footer)
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

# Fallback route to indicate feature in-progress
@app.route('/forgot-password')
def forgot_password_coming(): return "Coming soon..."

# Run server
if __name__ == '__main__':
    app.run(debug=True)