from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "secure_key"

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form['email']
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/create-profile', methods=['POST'])
def create_profile():
    # Get form data
    fname = request.form.get('fname')
    lname = request.form.get('lname')
    mobile = request.form.get('mobile')
    email = request.form.get('email')
    # Log for now
    print("Profile Created:", fname, lname, mobile, email)
    return redirect('/loan-request')

@app.route('/loan-request')
def loan_request():
    return render_template('loan_request.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template('dashboard.html', user=session['user'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
