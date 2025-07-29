from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = 'secure_key'

DATA_FILE = 'data.json'

# Initialize data file
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({'users': [], 'loan_requests': [], 'loan_counter': 19870000}, f)

def load_data():
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
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
            "monthly_salary": request.form['monthly_salary'],
            "other_income": request.form['other_income'],
            "address": request.form['address'],
            "cibil": request.form['cibil']
        }
        data = load_data()
        data['users'].append(user)
        session['user_email'] = user['email']
        session['mobile'] = user['mobile']
        save_data(data)
        return redirect('/loan-request')
    return render_template('signup.html')

@app.route('/loan-request', methods=['GET', 'POST'])
def loan_request():
    if 'user_email' not in session:
        return redirect('/login')

    if request.method == 'POST':
        data = load_data()
        data['loan_counter'] += 1
        loan_id = data['loan_counter']
        request_data = {
            "email": session['user_email'],
            "loan_id": loan_id,
            "loan_type": request.form['loan_type'],
            "amount": request.form['amount'],
            "duration": request.form['duration'],
            "status": "In Process",
            "remarks": ""
        }
        data['loan_requests'].append(request_data)
        save_data(data)
        return render_template('thankyou.html', loan_id=loan_id)
    
    return render_template('loan_request.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        data = load_data()
        for user in data['users']:
            if user['email'] == email or user['mobile'] == email:
                session['user_email'] = user['email']
                session['mobile'] = user['mobile']
                if email == "mayuri.luhar@gmail.com":
                    return redirect('/admin')
                return redirect('/dashboard')
        return "Invalid user!"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_email' not in session:
        return redirect('/login')
    data = load_data()
    loans = [l for l in data['loan_requests'] if l['email'] == session['user_email']]
    return render_template('dashboard.html', user_email=session['user_email'], loans=loans)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('user_email') != 'mayuri.luhar@gmail.com':
        return redirect('/login')
    
    data = load_data()
    
    if request.method == 'POST':
        loan_id = int(request.form['loan_id'])
        status = request.form['status']
        remarks = request.form['remarks']

        for loan in data['loan_requests']:
            if loan['loan_id'] == loan_id:
                loan['status'] = status
                loan['remarks'] = remarks
                break
        save_data(data)
        return redirect('/admin')
    
    return render_template('admin.html', loans=data['loan_requests'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
