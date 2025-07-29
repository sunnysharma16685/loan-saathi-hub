from flask import Flask, render_template, redirect, request, session, url_for
import json
import os

app = Flask(__name__)
app.secret_key = "secure_key"

# Load and Save JSON
def load_data():
    if not os.path.exists("data.json"):
        return {"users": [], "loans": [], "loanCounter": 19870000}
    with open("data.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

@app.route('/')
def index():
    return redirect('/home')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = load_data()
        form = request.form

        user = {
            "first_name": form['first_name'],
            "last_name": form['last_name'],
            "dob": form['dob'],
            "email": form['email'],
            "mobile": form['mobile'],
            "pan": form['pan'],
            "aadhaar": form['aadhaar'],
            "education": form['education'],
            "job": form['job'],
            "salary": form['salary'],
            "income": form['income'],
            "address": form['address'],
            "city": form['city'],
            "state": form['state'],
            "cibil": form['cibil']
        }

        data['users'].append(user)
        save_data(data)

        session['user'] = user['email']
        session['name'] = user['first_name'] + " " + user['last_name']

        return redirect('/loan-request')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        data = load_data()
        for user in data['users']:
            if user['email'] == email:
                session['user'] = user['email']
                session['name'] = user['first_name'] + " " + user['last_name']
                return redirect('/dashboard')
        return "User not found"
    return render_template('login.html')

@app.route('/loan-request', methods=['GET', 'POST'])
def loan_request():
    if 'user' not in session:
        return redirect('/login')

    data = load_data()
    if request.method == 'POST':
        loan_id = data['loanCounter'] + 1
        loan = {
            "loanId": loan_id,
            "email": session['user'],
            "name": session['name'],
            "loanType": request.form['loan_type'],
            "amount": request.form['amount'],
            "duration": request.form['duration'],
            "status": "In Process",
            "remark": ""
        }
        data['loans'].append(loan)
        data['loanCounter'] = loan_id
        save_data(data)
        return render_template('thankyou.html', loan_id=loan_id)
    
    return render_template('loan_request.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    data = load_data()
    user_loans = [loan for loan in data['loans'] if loan['email'] == session['user']]
    return render_template('dashboard.html', name=session['name'], loans=user_loans)

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
