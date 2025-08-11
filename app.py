import os
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Set SUPABASE_URL and SUPABASE_KEY in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key")

# Helper: generate random custom ID for loans or agents
def generate_custom_id(prefix):
    return f"{prefix}{random.randint(100000, 999999)}"

# Decorator for role-based login required
def login_required(role=None):
    def wrapper(fn):
        def decorated_view(*args, **kwargs):
            if 'user' not in session:
                flash("Please login first.", "error")
                return redirect(url_for("login"))
            if role and session['user']['role'] != role:
                flash("Unauthorized access.", "error")
                return redirect(url_for("index"))
            return fn(*args, **kwargs)
        decorated_view.__name__ = fn.__name__
        return decorated_view
    return wrapper

@app.route("/")
def index():
    if 'user' in session:
        role = session['user']['role']
        if role == 'user':
            return redirect(url_for('dashboard_user'))
        elif role == 'agent':
            return redirect(url_for('dashboard_agent'))
        elif role == 'admin':
            return redirect(url_for('dashboard_admin'))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email").lower()
        mobile = request.form.get("mobile")
        password = request.form.get("password")
        role = request.form.get("role")  # user / agent

        if not all([first_name, email, mobile, password, role]):
            flash("Please fill all required fields.", "error")
            return redirect(url_for("register"))

        # Check if user exists already
        existing = supabase.table("users").select("*").or_(f"email.eq.{email},mobile.eq.{mobile}").execute()
        if existing.data and len(existing.data) > 0:
            flash("User with this email or mobile already exists. Please login.", "error")
            return redirect(url_for("login"))

        password_hash = generate_password_hash(password)

        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "mobile": mobile,
            "password_hash": password_hash,
            "role": role,
            "created_at": "now()",
            "is_active": True
        }

        try:
            supabase.table("users").insert(user_data).execute()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            app.logger.error(f"Error during registration: {e}")
            flash("Something went wrong. Please try again later.", "error")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_id = request.form.get("login_id").lower()
        password = request.form.get("password")

        # Search user by email or mobile
        result = supabase.table("users").select("*").or_(f"email.eq.{login_id},mobile.eq.{login_id}").execute()
        users = result.data if result else []

        if not users:
            flash("User not found.", "error")
            return redirect(url_for("login"))

        user = users[0]
        if not user.get("is_active", True):
            flash("User is inactive. Contact admin.", "error")
            return redirect(url_for("login"))

        if check_password_hash(user["password_hash"], password):
            session["user"] = {
                "id": user["id"],
                "first_name": user["first_name"],
                "email": user["email"],
                "mobile": user["mobile"],
                "role": user["role"]
            }
            flash(f"Welcome {user['first_name']}!", "success")
            # Redirect based on role
            if user["role"] == "user":
                return redirect(url_for("dashboard_user"))
            elif user["role"] == "agent":
                return redirect(url_for("dashboard_agent"))
            elif user["role"] == "admin":
                return redirect(url_for("dashboard_admin"))
        else:
            flash("Incorrect password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("index"))

# Dashboard user
@app.route("/dashboard/user")
@login_required(role="user")
def dashboard_user():
    user = session["user"]
    # Fetch user's loan requests from Supabase
    try:
        res = supabase.table("loan_requests").select("*").eq("user_email", user["email"]).order("created_at", desc=True).execute()
        loans = res.data if res and res.data else []
    except Exception as e:
        app.logger.error(f"Error fetching loans: {e}")
        loans = []
    return render_template("dashboard_user.html", user=user, loans=loans)

# Dashboard agent
@app.route("/dashboard/agent")
@login_required(role="agent")
def dashboard_agent():
    user = session["user"]
    # Fetch leads assigned or all loan requests (customize as per your logic)
    try:
        res = supabase.table("loan_requests").select("*").order("created_at", desc=True).execute()
        loans = res.data if res and res.data else []
    except Exception as e:
        app.logger.error(f"Error fetching loans: {e}")
        loans = []
    return render_template("dashboard_agent.html", user=user, loans=loans)

# Dashboard admin
@app.route("/dashboard/admin")
@login_required(role="admin")
def dashboard_admin():
    user = session["user"]
    # Fetch all users, loans etc.
    try:
        users_res = supabase.table("users").select("*").execute()
        loans_res = supabase.table("loan_requests").select("*").execute()
        users = users_res.data if users_res and users_res.data else []
        loans = loans_res.data if loans_res and loans_res.data else []
    except Exception as e:
        app.logger.error(f"Error fetching admin data: {e}")
        users = []
        loans = []
    return render_template("dashboard_admin.html", user=user, users=users, loans=loans)

# Loan request
@app.route("/loan-request", methods=["GET", "POST"])
@login_required(role="user")
def loan_request():
    if request.method == "POST":
        loan_type = request.form.get("loan_type")
        amount = request.form.get("amount")
        duration = request.form.get("duration")
        pincode = request.form.get("pincode")
        city = request.form.get("city")
        state = request.form.get("state")
        pan = request.form.get("pan")
        aadhar = request.form.get("aadhar")
        itr = request.form.get("itr")
        cibil = request.form.get("cibil")

        # Basic validation
        if not all([loan_type, amount, duration, pincode, city, state, pan, itr]):
            flash("Please fill all mandatory fields.", "error")
            return redirect(url_for("loan_request"))

        loan_id = generate_custom_id("LN")

        loan_data = {
            "loan_id": loan_id,
            "user_email": session["user"]["email"],
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
            "status": "In Process",
            "created_at": "now()"
        }

        try:
            supabase.table("loan_requests").insert(loan_data).execute()
            flash("Loan request submitted successfully!", "success")
            return render_template("thankyou.html", loan_id=loan_id)
        except Exception as e:
            app.logger.error(f"Error submitting loan request: {e}")
            flash("Error submitting loan request. Try again.", "error")
            return redirect(url_for("loan_request"))

    return render_template("loan_request.html")

# Static pages
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

@app.route("/forgot", methods=["GET", "POST"])
def forgot():
    if request.method == "POST":
        email_or_mobile = request.form.get("email_or_mobile")
        # Implement actual forgot password logic here or send email
        flash(f"If {email_or_mobile} exists, reset instructions have been sent.", "success")
        return redirect(url_for("login"))
    return render_template("forgot.html")

if __name__ == "__main__":
    app.run(debug=True)
