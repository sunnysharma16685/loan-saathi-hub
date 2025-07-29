from flask import Flask, render_template, request, redirect, session
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATA_FILE = 'data.json'

# Load and save data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        return {'users': [], 'loans': [], 'loanCounter': 19870000}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def home():
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup():
    data = load_data()

    user = {
        "first_name": request.form['first_name'],
        "last_name": request.form['last_name'],
        "dob": request.form['dob'],
        "city": request.form['city'],
        "state": request.form['state'],
        "mobile": request.form['mobile'],
        "email": request.form['email'],
        "pan": request.form['pan'],
        "aadhaar": request.form['aadhaar'],
        "education": request.form['education'],
        "job": request.form['job'],
        "salary_mode": request.form['salary_mode'],
        "income": request.form['income'],
        "address": request.form['address'],
        "cibil": request.form['cibil']
    }

    session['user'] = user['email']
    data['users'].append(user)
    save_data(data)

    return redirect('/loan-request')

@app.route('/loan-request', methods=['GET', 'POST'])
def loan_request():
    if 'user' not in session:
        return redirect('/')

    data = load_data()

    if request.method == 'POST':
        data['loanCounter'] += 1
        loan = {
            "email": session['user'],
            "loanType": request.form['loan_type'],
            "amount": request.form['amount'],
            "duration": request.form['duration'],
            "loanId": data['loanCounter'],
            "status": "In Process",
            "remark": ""
        }
        data['loans'].append(loan)
        save_data(data)
        return render_template('thankyou.html', loan_id=loan['loanId'])

    return render_template('loan_request.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form['email']
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    data = load_data()
    user_loans = [l for l in data['loans'] if l['email'] == session['user']]
    return render_template('dashboard.html', loans=user_loans)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ✅ Admin Panel Route
@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if session.get('user') != "mayuri.luhar@gmail.com":
        return "❌ Unauthorized Access", 403

    data = load_data()
    loans = data['loans']

    if request.method == 'POST':
        loan_id = request.form['loan_id']
        action = request.form['action']
        remark = request.form['remark']

        for loan in loans:
            if str(loan['loanId']) == loan_id:
                loan['status'] = action
                loan['remark'] = remark
                break
        save_data(data)
        return redirect('/admin')

    return render_template('admin.html', loans=loans)

if __name__ == '__main__':
    app.run(debug=True)
