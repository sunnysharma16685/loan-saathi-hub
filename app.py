from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
from supabase import create_client, Client

SUPABASE_URL = "https://cokxynyddbloupedszoj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = 'secure_key'

DATA_FILE = 'data.json'

# Utility functions
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    return {"users": [], "loan_requests": []}

def save_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

def generate_loan_id():
    data = load_data()
    existing = [int(lr["loan_id"]) for lr in data["loan_requests"]] if data["loan_requests"] else []
    next_id = max(existing, default=19870000) + 1
    return str(next_id)

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = {
            "first_name": request.form['first_name'],
            "last_name": request.form['last_name'],
            "email": request.form['email'],
            "mobile": request.form['mobile']
        }
        session['user'] = user
        return redirect(url_for('create_profile'))
    return render_template('signup.html')

@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    if 'user' not in session:
        return redirect('/signup')
    if request.method == 'POST':
        data = load_data()
        user = session['user']
        user.update({
            "dob": request.form['dob'],
            "city": request.form['city'],
            "state": request.form['state'],
            "pan": request.form['pan'],
            "aadhaar": request.form['aadhaar'],
            "education": request.form['education'],
            "job": request.form['job'],
            "salary_mode": request.form['salary_mode'],
            "monthly_income": request.form['monthly_income'],
            "other_income": request.form['other_income'],
            "address": request.form['address'],
            "cibil": request.form['cibil']
        })
        data["users"].append(user)
        save_data(data)
        return redirect('/loan-request')
    return render_template('create_profile.html')

@app.route('/loan-request', methods=['GET', 'POST'])
def loan_request():
    if 'user' not in session:
        return redirect('/signup')
    if request.method == 'POST':
        data = load_data()
        loan = {
            "loan_id": generate_loan_id(),
            "email": session['user']['email'],
            "loan_type": request.form['loan_type'],
            "amount": request.form['amount'],
            "duration": request.form['duration'],
            "status": "In-process",
            "remarks": ""
        }
        data["loan_requests"].append(loan)
        save_data(data)
        return render_template('thankyou.html', loan_id=loan["loan_id"])
    return render_template('loan_request.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        mobile = request.form['mobile']
        data = load_data()
        user = next((u for u in data["users"] if u["email"] == email and u["mobile"] == mobile), None)
        if user:
            session['user'] = user
            return redirect('/dashboard')
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    data = load_data()
    user_loans = [lr for lr in data["loan_requests"] if lr["email"] == session['user']['email']]
    return render_template('dashboard.html', user=session['user'], loans=user_loans)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Admin routes
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['email'] == 'admin@loansaathihub.in':
            session['admin'] = True
            return redirect('/admin-dashboard')
        else:
            return "Unauthorized"
    return render_template('admin_login.html')

@app.route('/admin-dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin-login')
    data = load_data()
    if request.method == 'POST':
        loan_id = request.form['loan_id']
        action = request.form['action']
        remarks = request.form.get('remarks', '')
        for lr in data['loan_requests']:
            if lr['loan_id'] == loan_id:
                lr['status'] = 'Approved' if action == 'approve' else 'Rejected'
                lr['remarks'] = remarks
                break
        save_data(data)
    return render_template('admin_dashboard.html', loans=data["loan_requests"])

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        return "Recovery link sent to your email/mobile (mock)"
    return render_template('forgot.html')

if __name__ == '__main__':
    app.run(debug=True)
