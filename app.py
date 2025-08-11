import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Set SUPABASE_URL and SUPABASE_KEY in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Decorator for login required with role checking
def login_required(role=None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if "user" not in session:
                flash("Please login first.", "error")
                return redirect(url_for("login"))
            if role and session["user"]["role"] != role:
                flash("Unauthorized access.", "error")
                return redirect(url_for("index"))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

# Index - home page
@app.route("/")
def index():
    if "user" in session:
        role = session["user"]["role"]
        if role == "user":
            return redirect(url_for("dashboard_user"))
        elif role == "agent":
            return redirect(url_for("dashboard_agent"))
        elif role == "admin":
            return redirect(url_for("dashboard_admin"))
    return render_template("index.html")

# Login route for all
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_id = request.form.get("login_id")
        password = request.form.get("password")

        # Try to find user/agent/admin in Supabase
        for table_name, role_name in [("users", "user"), ("agents", "agent"), ("admins", "admin")]:
            res = supabase.table(table_name).select("*").or_(f"email.eq.{login_id},mobile.eq.{login_id}").execute()
            if res.data:
                user = res.data[0]
                if user.get("password") == password:
                    session["user"] = {
                        "id": user["id"],
                        "first_name": user.get("first_name"),
                        "last_name": user.get("last_name"),
                        "email": user.get("email"),
                        "mobile": user.get("mobile"),
                        "role": role_name
                    }
                    flash(f"Welcome {user.get('first_name')}!", "success")
                    if role_name == "user":
                        return redirect(url_for("dashboard_user"))
                    elif role_name == "agent":
                        return redirect(url_for("dashboard_agent"))
                    elif role_name == "admin":
                        return redirect(url_for("dashboard_admin"))
                else:
                    flash("Incorrect password.", "error")
                    return redirect(url_for("login"))
        flash("User not found.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("index"))

# User dashboard with loan requests table
@app.route("/dashboard/user")
@login_required(role="user")
def dashboard_user():
    user_id = session["user"]["id"]
    user = supabase.table("users").select("*").eq("id", user_id).single().execute().data

    loans = supabase.table("loan_requests").select("*").eq("user_id", user_id).execute().data or []

    return render_template("dashboard_user.html", user=user, loans=loans)

# Agent dashboard with leads table
@app.route("/dashboard/agent")
@login_required(role="agent")
def dashboard_agent():
    agent_id = session["user"]["id"]
    agent = supabase.table("agents").select("*").eq("id", agent_id).single().execute().data

    # Show loans with status Pending or Active for this agent's city or all?
    loans = supabase.table("loan_requests").select("*").execute().data or []

    # You can filter based on city or agent's assigned leads here

    return render_template("dashboard_agent.html", agent=agent, loans=loans)

# Admin dashboard
@app.route("/dashboard/admin")
@login_required(role="admin")
def dashboard_admin():
    users = supabase.table("users").select("*").execute().data or []
    agents = supabase.table("agents").select("*").execute().data or []
    loans = supabase.table("loan_requests").select("*").execute().data or []
    payments = supabase.table("payments").select("*").execute().data or []

    total_users = len(users)
    total_agents = len(agents)
    total_loans_applied = len(loans)
    total_loans_rejected = len([l for l in loans if l.get('status') == 'Rejected'])
    total_loans_approved = len([l for l in loans if l.get('status') == 'Approved'])
    total_payments_received = sum([p.get('amount',0) for p in payments])

    return render_template("dashboard_admin.html",
                           users=users,
                           agents=agents,
                           total_users=total_users,
                           total_agents=total_agents,
                           total_loans_applied=total_loans_applied,
                           total_loans_rejected=total_loans_rejected,
                           total_loans_approved=total_loans_approved,
                           total_payments_received=total_payments_received
    )

# Registration basic form (index page handles basic user/agent sign-up form and redirects to complete profile)
@app.route("/register/basic", methods=["POST"])
def register_basic():
    user_type = request.form.get("user_type")  # 'user' or 'agent'
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    mobile = request.form.get("mobile")
    email = request.form.get("email")

    # Check if email or mobile already exist in either users or agents
    for table_name in ["users", "agents"]:
        res = supabase.table(table_name).select("*").or_(f"email.eq.{email},mobile.eq.{mobile}").execute()
        if res.data:
            flash(f"{user_type.capitalize()} already registered with this email or mobile.", "error")
            return redirect(url_for("index"))

    # Save basic info in session for next step profile complete
    session["basic_profile"] = {
        "user_type": user_type,
        "first_name": first_name,
        "last_name": last_name,
        "mobile": mobile,
        "email": email
    }

    if user_type == "user":
        return redirect(url_for("complete_profile_user"))
    else:
        return redirect(url_for("complete_profile_agent"))

# Complete profile for user
@app.route("/profile/user", methods=["GET", "POST"])
def complete_profile_user():
    if "basic_profile" not in session or session["basic_profile"]["user_type"] != "user":
        flash("Complete basic registration first.", "error")
        return redirect(url_for("index"))

    data = session["basic_profile"]

    if request.method == "POST":
        # Collect form data and insert into Supabase
        profile_data = {
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "mobile": data["mobile"],
            "email": data["email"],
            "address1": request.form.get("address1"),
            "address2": request.form.get("address2"),
            "pin_code": request.form.get("pin_code"),
            "city": request.form.get("city"),
            "state": request.form.get("state"),
            "pan_number": request.form.get("pan_number"),
            "aadhar_number": request.form.get("aadhar_number"),
            "itr": request.form.get("itr"),
            "cibil_score": request.form.get("cibil_score"),
            "job_or_business": request.form.get("job_or_business"),
            # Job fields
            "job_type": request.form.get("job_type"),
            "employment_type": request.form.get("employment_type"),
            "company_name": request.form.get("company_name"),
            "designation": request.form.get("designation"),
            "total_experience": request.form.get("total_experience"),
            "current_company_experience": request.form.get("current_company_experience"),
            "salary_mode": request.form.get("salary_mode"),
            "monthly_salary": request.form.get("monthly_salary"),
            "other_income": request.form.get("other_income"),
            # Business fields
            "business_turnover": request.form.get("business_turnover"),
            "business_designation": request.form.get("business_designation"),
        }

        # Insert into Supabase users table
        supabase.table("users").insert(profile_data).execute()

        # Clear session basic_profile
        session.pop("basic_profile", None)

        flash("Profile completed successfully!", "success")
        return redirect(url_for("dashboard_user"))

    return render_template("complete_profile_user.html", data=data)

# Complete profile for agent
@app.route("/profile/agent", methods=["GET", "POST"])
def complete_profile_agent():
    if "basic_profile" not in session or session["basic_profile"]["user_type"] != "agent":
        flash("Complete basic registration first.", "error")
        return redirect(url_for("index"))

    data = session["basic_profile"]

    if request.method == "POST":
        profile_data = {
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "mobile": data["mobile"],
            "email": data["email"],
            "agent_type": request.form.get("agent_type"),
            # DSA details
            "dsa_code": request.form.get("dsa_code"),
            "bank_name": request.form.get("bank_name"),
            "branch": request.form.get("branch"),
            # Bank/Finance details
            "bank_finance_name": request.form.get("bank_finance_name"),
            "bank_finance_branch": request.form.get("bank_finance_branch"),
            "designation": request.form.get("designation"),
            # Private firm details
            "firm_name": request.form.get("firm_name"),
            "gst_number": request.form.get("gst_number"),
            "firm_address": request.form.get("firm_address"),
            "pin_code": request.form.get("pin_code"),
            "city": request.form.get("city"),
            "state": request.form.get("state"),
        }

        supabase.table("agents").insert(profile_data).execute()
        session.pop("basic_profile", None)
        flash("Agent profile completed successfully!", "success")
        return redirect(url_for("dashboard_agent"))

    return render_template("complete_profile_agent.html", data=data)

# Loan request by user
@app.route("/loan-request", methods=["GET", "POST"])
@login_required(role="user")
def loan_request():
    if request.method == "POST":
        user_id = session["user"]["id"]
        loan_type = request.form.get("loan_type")
        amount = request.form.get("amount")
        duration = request.form.get("duration")
        reason = request.form.get("reason")

        loan_data = {
            "user_id": user_id,
            "loan_type": loan_type,
            "amount": amount,
            "duration": duration,
            "reason": reason,
            "status": "Pending"
        }
        supabase.table("loan_requests").insert(loan_data).execute()

        flash("Loan request submitted successfully.", "success")
        return redirect(url_for("dashboard_user"))
    return render_template("loan_request.html")

# Admin routes and actions for updating users and agents status

@app.route('/admin/user/<int:user_id>/update_status', methods=['POST'])
@login_required(role='admin')
def update_user_status(user_id):
    action = request.form.get('action')
    if action == 'delete':
        supabase.table("users").delete().eq("id", user_id).execute()
        flash("User deleted successfully.", "success")
    elif action in ['reactive', 'active']:
        supabase.table("users").update({"status": "Active"}).eq("id", user_id).execute()
        flash("User activated/reactivated.", "success")
    return redirect(url_for('dashboard_admin'))

@app.route('/admin/agent/<int:agent_id>/update_status', methods=['POST'])
@login_required(role='admin')
def update_agent_status(agent_id):
    action = request.form.get('action')
    if action == 'delete':
        supabase.table("agents").delete().eq("id", agent_id).execute()
        flash("Agent deleted successfully.", "success")
    elif action in ['reactive', 'active']:
        supabase.table("agents").update({"status": "Active"}).eq("id", agent_id).execute()
        flash("Agent activated/reactivated.", "success")
    return redirect(url_for('dashboard_admin'))

@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/support")
def support():
    return render_template("support.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")


# Run app
if __name__ == "__main__":
    app.run(debug=True)
