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


# ----------------------- Signup -----------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form

        # Insert user into Supabase
        supabase.table("users").insert({
            "first_name": data['first_name'],
            "last_name": data['last_name'],
            "dob": data['dob'],
            "city": data['city'],
            "state": data['state'],
            "mobile": data['mobile'],
            "email": data['email'],
            "pan": data['pan'],
            "aadhaar": data['aadhaar'],
            "education": data['education'],
            "job": data['job'],
            "salary_mode": data['salary_mode'],
            "monthly_income": data['monthly_income'],
            "other_income": data['other_income'],
            "address": data['address'],
            "cibil": data['cibil']
        }).execute()

        # Set session and redirect
        session['user'] = data['email']
        session['mobile'] = data['mobile']
        return redirect('/loan-request')
    return render_template('signup.html')


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


# ----------------------- Run App -----------------------
if __name__ == '__main__':
    app.run(debug=True)
