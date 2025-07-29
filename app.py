from flask import Flask, render_template, redirect, request, session, url_for

app = Flask(__name__)
app.secret_key = "secure_key"

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form['email']
        return redirect('/dashboard')
    return render_template('login.html')

# Dashboard Page
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    return render_template('dashboard.html', user=session['user'])

# Apply Loan Page
@app.route('/apply-loan', methods=['GET', 'POST'])
def apply_loan():
    if 'user' not in session:
        return redirect('/login')
    if request.method == 'POST':
        amount = request.form['amount']
        tenure = request.form['tenure']
        print(f"User {session['user']} applied for ₹{amount} loan for {tenure} months.")
        return redirect('/dashboard')
    return render_template('apply_loan.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
