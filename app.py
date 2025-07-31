from flask import Flask, render_template, request, redirect, session, url_for
from supabase import create_client, Client
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Supabase credentials
url = "https://cokxynyddbloupedszoj.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
supabase: Client = create_client(url, key)

# ----------------------- Home -----------------------
@app.route('/')
def home():
    return render_template('home.html')


# ----------------------- Signup & Profile Creation -----------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
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
        latest = supabase.table("loan_requests").select("loan_id").order("loan_id", desc=True).limit(1).execute()
        last_id = int(latest.data[0]['loan_id']) if latest.data else 19870000
        new_loan_id = str(last_id + 1)

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
        supabase.table("loan_requests").update({
            "status": status,
            "remark": remark
        }).eq("loan_id", loan_id).execute()

    res = supabase.table("loan_requests").select("*").execute()
    return render_template('admin_dashboard.html', loans=res.data)


# ----------------------- Run the App -----------------------
if __name__ == '__main__':
    app.run(debug=True)
