
from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "secure_key"

users = {}
loans = []
loan_counter = 19870000

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        mobile = request.form['mobile']
        email = request.form['email']
        users[mobile] = {
            'email': email,
            'first_name': request.form['first_name'],
            'last_name': request.form['last_name'],
        }
        session['user'] = mobile
        return redirect('/apply-loan')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        if identifier in users or any(u['email'] == identifier for u in users.values()):
            session['user'] = identifier
            return redirect('/dashboard')
        return "User not found"
    return render_template('login.html')

@app.route('/apply-loan', methods=['GET', 'POST'])
def apply_loan():
    global loan_counter
    if 'user' not in session:
        return redirect('/login')
    if request.method == 'POST':
        loan_counter += 1
        loans.append({
            'loan_id': loan_counter,
            'user': session['user'],
            'type': request.form['loan_type'],
            'amount': request.form['amount'],
            'status': 'In Process',
            'remarks': ''
        })
        return render_template('thankyou.html', loan_id=loan_counter)
    return render_template('apply_loan.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    user_loans = [loan for loan in loans if loan['user'] == session['user']]
    return render_template('dashboard.html', user=session['user'], loans=user_loans)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
