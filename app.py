# app.py
import os
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_KEY in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ---------------------------
# Helpers & decorators
# ---------------------------
def login_required(role=None):
    def wrapper(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            if "user" not in session:
                flash("Please login first.", "error")
                return redirect(url_for("login"))
            if role and session["user"].get("role") != role:
                flash("Unauthorized.", "error")
                return redirect(url_for("index"))
            return fn(*args, **kwargs)
        return inner
    return wrapper

def exists_in_table(table, email=None, mobile=None):
    # Check email
    if email:
        res = supabase.table(table).select("id").eq("email", email).execute()
        if res and getattr(res, "data", None):
            return True
    if mobile:
        res = supabase.table(table).select("id").eq("mobile", mobile).execute()
        if res and getattr(res, "data", None):
            return True
    return False

# ---------------------------
# Routes
# ---------------------------
@app.route("/")
def index():
    # If logged in, redirect to respective dashboard
    if "user" in session:
        role = session["user"].get("role")
        if role == "user":
            return redirect(url_for("dashboard_user"))
        if role == "agent":
            return redirect(url_for("dashboard_agent"))
        if role == "admin":
            return redirect(url_for("dashboard_admin"))
    return render_template("index.html")


# Basic registration (index form posts here)
@app.route("/register/basic", methods=["POST"])
def register_basic():
    user_type = request.form.get("user_type")  # user or agent
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    mobile = request.form.get("mobile", "").strip()
    email = request.form.get("email", "").strip()

    if not (first_name and last_name and mobile and email and user_type):
        flash("Please fill all fields.", "error")
        return redirect(url_for("index"))

    # Check duplicates in users or agents
    for t in ("users", "agents"):
        if exists_in_table(t, email=email, mobile=mobile):
            flash(f"Already registered (found in {t}). Please login.", "error")
            return redirect(url_for("index"))

    session["basic_profile"] = dict(
        user_type=user_type,
        first_name=first_name,
        last_name=last_name,
        mobile=mobile,
        email=email,
    )

    if user_type == "user":
        return redirect(url_for("complete_profile_user"))
    else:
        return redirect(url_for("complete_profile_agent"))


# Complete profile - User
@app.route("/profile/user", methods=["GET", "POST"])
def complete_profile_user():
    bp = session.get("basic_profile")
    if not bp or bp.get("user_type") != "user":
        flash("Start from the home page registration.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        # Collect profile details
        profile_data = {
            "first_name": bp["first_name"],
            "last_name": bp["last_name"],
            "email": bp["email"],
            "mobile": bp["mobile"],
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
            "job_type": request.form.get("job_type"),
            "employment_type": request.form.get("employment_type"),
            "company_name": request.form.get("company_name"),
            "designation": request.form.get("designation"),
            "total_experience": request.form.get("total_experience"),
            "current_company_experience": request.form.get("current_company_experience"),
            "salary_mode": request.form.get("salary_mode"),
            "monthly_salary": request.form.get("monthly_salary"),
            "other_income": request.form.get("other_income"),
            "business_turnover": request.form.get("business_turnover"),
            "business_designation": request.form.get("business_designation"),
        }
        res = supabase.table("users").insert(profile_data).execute()
        inserted = getattr(res, "data", None)
        if inserted:
            user_row = inserted[0]
            # create session user
            session["user"] = dict(
                id=user_row.get("id"),
                first_name=user_row.get("first_name"),
                email=user_row.get("email"),
                role="user",
            )
            session.pop("basic_profile", None)
            flash("Profile created — welcome!", "success")
            return redirect(url_for("dashboard_user"))
        else:
            flash("Error saving profile. Try again.", "error")
            return redirect(url_for("complete_profile_user"))

    # GET: render with pre-filled basic data
    return render_template("complete_profile_user.html", data=bp)


# Complete profile - Agent
@app.route("/profile/agent", methods=["GET", "POST"])
def complete_profile_agent():
    bp = session.get("basic_profile")
    if not bp or bp.get("user_type") != "agent":
        flash("Start from the home page registration.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        profile_data = {
            "first_name": bp["first_name"],
            "last_name": bp["last_name"],
            "email": bp["email"],
            "mobile": bp["mobile"],
            "agent_type": request.form.get("agent_type"),
            "dsa_code": request.form.get("dsa_code"),
            "bank_name": request.form.get("bank_name"),
            "branch": request.form.get("branch"),
            "bank_finance_name": request.form.get("bank_finance_name"),
            "bank_finance_branch": request.form.get("bank_finance_branch"),
            "designation": request.form.get("designation"),
            "firm_name": request.form.get("firm_name"),
            "gst_number": request.form.get("gst_number"),
            "firm_address": request.form.get("firm_address"),
            "pin_code": request.form.get("pin_code"),
            "city": request.form.get("city"),
            "state": request.form.get("state"),
        }
        res = supabase.table("agents").insert(profile_data).execute()
        inserted = getattr(res, "data", None)
        if inserted:
            agent_row = inserted[0]
            session["user"] = dict(
                id=agent_row.get("id"),
                first_name=agent_row.get("first_name"),
                email=agent_row.get("email"),
                role="agent",
            )
            session.pop("basic_profile", None)
            flash("Agent profile created — welcome!", "success")
            return redirect(url_for("dashboard_agent"))
        else:
            flash("Error saving agent profile. Try again.", "error")
            return redirect(url_for("complete_profile_agent"))

    return render_template("complete_profile_agent.html", data=bp)


# Login (user/agent/admin)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_id = request.form.get("identifier", "").strip()
        password = request.form.get("password", "").strip()  # plaintext for demo (not secure)
        # Try admins, agents, users (in that order)
        for table, role in (("admins", "admin"), ("agents", "agent"), ("users", "user")):
            # first try by email
            res = supabase.table(table).select("*").eq("email", login_id).execute()
            data = getattr(res, "data", None)
            if not data:
                # try by mobile
                res = supabase.table(table).select("*").eq("mobile", login_id).execute()
                data = getattr(res, "data", None)
            if data:
                row = data[0]
                # NOTE: using plaintext passwords for demo. In prod, compare hashed password.
                if (row.get("password") or "") == password:
                    session["user"] = dict(
                        id=row.get("id"),
                        first_name=row.get("first_name"),
                        email=row.get("email"),
                        role=role
                    )
                    flash("Login successful.", "success")
                    if role == "admin":
                        return redirect(url_for("dashboard_admin"))
                    elif role == "agent":
                        return redirect(url_for("dashboard_agent"))
                    else:
                        return redirect(url_for("dashboard_user"))
                else:
                    flash("Incorrect password.", "error")
                    return redirect(url_for("login"))
        flash("User not found.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("index"))


# User dashboard
@app.route("/dashboard/user")
@login_required(role="user")
def dashboard_user():
    user_id = session["user"]["id"]
    # fetch user row (optional)
    user_row = supabase.table("users").select("*").eq("id", user_id).single().execute().data
    loans = supabase.table("loan_requests").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data or []
    return render_template("dashboard_user.html", user=user_row, loans=loans)


# Agent dashboard
@app.route("/dashboard/agent")
@login_required(role="agent")
def dashboard_agent():
    agent_id = session["user"]["id"]
    agent_row = supabase.table("agents").select("*").eq("id", agent_id).single().execute().data
    # Show all pending loans (you can filter by city etc)
    loans = supabase.table("loan_requests").select("*").order("created_at", desc=True).execute().data or []
    return render_template("dashboard_agent.html", agent=agent_row, loans=loans)


# Loan request (user)
@app.route("/loan-request", methods=["GET", "POST"])
@login_required(role="user")
def loan_request():
    if request.method == "POST":
        user_id = session["user"]["id"]
        loan_type = request.form.get("loan_type")
        amount = request.form.get("amount")
        duration = request.form.get("duration")
        reason = request.form.get("reason")
        payload = {
            "user_id": user_id,
            "loan_type": loan_type,
            "amount": amount,
            "duration": duration,
            "reason": reason,
            "status": "Pending"
        }
        supabase.table("loan_requests").insert(payload).execute()
        flash("Loan request submitted.", "success")
        return redirect(url_for("dashboard_user"))
    return render_template("loan_request.html")


# Agent opens loan -> view profile (mark Active)
@app.route("/loan/<int:loan_id>/view")
@login_required(role="agent")
def view_loan(loan_id):
    # fetch loan and user
    loan_res = supabase.table("loan_requests").select("*").eq("id", loan_id).single().execute()
    loan = getattr(loan_res, "data", None)
    if not loan:
        flash("Loan not found.", "error")
        return redirect(url_for("dashboard_agent"))
    loan = loan_res.data
    user_row = supabase.table("users").select("*").eq("id", loan.get("user_id")).single().execute().data
    # mark active and attach agent
    supabase.table("loan_requests").update({"status": "Active", "agent_id": session["user"]["id"]}).eq("id", loan_id).execute()
    return render_template("loan_profile_view.html", loan=loan, user=user_row)


# Agent approve or reject (with remark)
@app.route("/loan/<int:loan_id>/action", methods=["POST"])
@login_required(role="agent")
def loan_action(loan_id):
    action = request.form.get("action")  # approve or reject
    remark = request.form.get("remark")
    update_payload = {"remark": remark}
    if action == "approve":
        update_payload["status"] = "Approved"
    elif action == "reject":
        update_payload["status"] = "Rejected"
    supabase.table("loan_requests").update(update_payload).eq("id", loan_id).execute()
    flash("Action saved.", "success")
    return redirect(url_for("dashboard_agent"))


# Admin dashboard (counts)
@app.route("/dashboard/admin")
@login_required(role="admin")
def dashboard_admin():
    users = supabase.table("users").select("id").execute().data or []
    agents = supabase.table("agents").select("id").execute().data or []
    loans = supabase.table("loan_requests").select("id,status").execute().data or []
    payments = supabase.table("payments").select("amount").execute().data or []

    total_users = len(users)
    total_agents = len(agents)
    total_loans = len(loans)
    total_rejected = len([l for l in loans if l.get("status") == "Rejected"])
    total_approved = len([l for l in loans if l.get("status") == "Approved"])
    total_payments = sum([p.get("amount", 0) for p in payments])

    return render_template("dashboard_admin.html",
                           total_users=total_users,
                           total_agents=total_agents,
                           total_loans=total_loans,
                           total_rejected=total_rejected,
                           total_approved=total_approved,
                           total_payments=total_payments)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
