from flask import Flask, render_template, redirect, request, session, url_for

app = Flask(__name__)
app.secret_key = "secure_key"

# Initialize Loan ID (in-memory for now)
loan_id_counter = 19870000

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        mobile = request.form['mobile']
        session['user'] = {'email': email, 'mobile': mobile}
        return redirect('/dashboard')
    return render_template('login.html')

@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        session['profile'] = {
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
            'dob': request.form['dob'],
            'city': request.form['city'],
            'state': request.form['state'],
            'mobile': request.form['mobile'],
            'email': request.form['email'],
            'pan': request.form['pan'],
            'aadhaar': request.form['aadhaar'],
            'education': request.form['education'],
            'job': request.form['job'],
            'salary_mode': request.form['salary_mode'],
            'other_income': request.form['other_income'],
            'address': request.form['address'],
            'cibil': request.form['cibil']
        }
        return redirect('/loan-request')
    return render_template('create_profile.html')

@app.route('/loan-request', methods=['GET', 'POST'])
def loan_request():
    global loan_id_counter
    if 'user' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        loan_id_counter += 1
        session['loan'] = {
            'loan_type': request.form['loan_type'],
            'amount': request.form['amount'],
            'duration': request.form['duration'],
            'loan_id': loan_id_counter,
            'status': 'In Process',
            'remarks': '',
            'bank_rejected': []
        }
        return redirect('/dashboard')
    
    return render_template('loan_request.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template(
        'dashboard.html',
        user=session['user'],
        profile=session.get('profile'),
        loan=session.get('loan')
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
