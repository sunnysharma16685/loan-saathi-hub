from flask import Flask, render_template, request, redirect, session, url_for
import json
import os

app = Flask(__name__)
app.secret_key = "your_secure_key"

DATA_FILE = "data.json"

# Ensure data.json exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"users": [], "loans": [], "loan_counter": 19870000}, f)

def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        form = request.form
        data = load_data()
        user = {
            "name": form['first_name'] + " " + form['last_name'],
            "dob": form['dob'],
            "city": form['city'],
            "state": form['state'],
            "mobile": form['mobile'],
            "email": form['email'],
            "pan": form['pan'],
            "aadhaar": form['aadhaar'],
            "education": form['education'],
            "job": form['job'],
            "salary": form['salary'],
            "income": form['income'],
            "address": form['address'],
            "cibil": form['cibil']
        }
        data['users'].append(user)
        session['user'] = user
        save_data(data)
        return redirect('/loan-request')
    return render_template("signup.html")

@app.route('/loan-request', methods=['GET', 'POST'])
def loan_request():
    if request.method == 'POST':
        form = request.form
        data = load_data()
        user = session.get('user')
        data['loan_counter'] += 1
        loan = {
            "loan_id": data['loan_counter'],
            "email": user['email'],
            "loan_type": form['loan_type'],
            "amount": form['amount'],
            "duration": form['duration'],
            "status": "In Process",
            "remarks": ""
        }
        data['loans'].append(loan)
        save_data(data)
        return redirect('/thankyou')
    return render_template("loan_request.html")

@app.route('/thankyou')
def thankyou():
    return render_template("thankyou.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = load_data()
        email = request.form['email']
        mobile = request.form['mobile']
        for user in data['users']:
            if user['email'] == email and user['mobile'] == mobile:
                session['user'] = user
                return redirect('/dashboard')
        return "Invalid login"
    return render_template("login.html")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    data = load_data()
    user = session['user']
    loans = [l for l in data['loans'] if l['email'] == user['email']]
    return render_template("dashboard.html", user=user, loans=loans)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
