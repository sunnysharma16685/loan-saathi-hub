from flask import jsonify
dummy_otp_store = {}

from fpdf import FPDF
import io
from flask import send_file
from datetime import datetime

import os
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client
from dotenv import load_dotenv
from functools import wraps

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import decimal
# optional if using Razorpay
import razorpay


# load .env locally
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError('SUPABASE_URL and SUPABASE_KEY must be set (see .env)')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# --- helpers ---
def login_required(role=None):
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            if 'user' not in session:
                flash('Please login first.', 'warning')
                return redirect(url_for('login'))
            if role and session['user'].get('role') != role:
                flash('Unauthorized', 'danger')
                return redirect(url_for('index'))
            return fn(*args, **kwargs)
        return decorated
    return wrapper

# --- routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register/basic', methods=['POST'])
def register_basic():
    user_type = request.form.get('user_type') or request.form.get('role') or 'user'
    first_name = request.form.get('first_name')
    mobile = request.form.get('mobile')
    otp = (request.form.get('otp') or "").strip()
    email = request.form.get('email')
    password = request.form.get('password')
    password2 = request.form.get('password2')

    if not (first_name and mobile and email):
        flash('Please fill required fields', 'danger')
        return redirect(url_for('index'))

    if not password or password != password2:
        flash('Passwords do not match or empty', 'danger')
        return redirect(url_for('index'))

    if mobile not in dummy_otp_store or dummy_otp_store[mobile] != otp:
        flash("Invalid OTP. Please try again.", "danger")
        return redirect(url_for("index"))

    # OTP success - one-time use
    dummy_otp_store.pop(mobile, None)

    # Prepare data
    basic_data = {
        'user_type': user_type,
        'first_name': first_name,
        'last_name': request.form.get('last_name'),
        'mobile': mobile,
        'email': email,
        'password': password,  # dev only; prod me hash karo
        'created_at': datetime.utcnow().isoformat()
    }

    session['basic_profile'] = basic_data

    # Insert into Supabase safely
    try:
        table_name = "users_basic" if user_type == 'user' else "agents_basic"
        insert_result = supabase.table(table_name).insert(basic_data).execute()
    except Exception as e:
        print("Supabase insert error:", e)

    # Redirect to complete profile page
    if user_type == 'user':
        return render_template('complete_profile_user.html', data=basic_data)
    else:
        return render_template('complete_profile_agent.html', data=basic_data)


@app.route("/send_otp", methods=["POST"])
def send_otp():
    mobile = (request.form.get("mobile") or "").strip()
    if not (mobile.isdigit() and len(mobile) == 10):
        return jsonify(ok=False, message="Invalid mobile number"), 400

    # Dummy OTP (dev only)
    otp = str(random.randint(100000, 999999))
    dummy_otp_store[mobile] = otp

    # NOTE: Prod me OTP ko kabhi response me na bhejein. Yahan demo ke liye dikha rahe hain.
    return jsonify(ok=True, message=f"OTP sent (dummy): {otp}", otp=otp)

@app.route('/profile/user', methods=['GET', 'POST'])
def complete_profile_user():
    data = session.get('basic_profile')
    if not data or data.get('user_type') != 'user':
        flash('Start registration first.', 'warning')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Basic + Complete profile payload
        payload = {
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'mobile': data['mobile'],
            'password_hash': data['password'],
            'email': data['email'],
            'address1': request.form.get('address1'),
            'address2': request.form.get('address2'),
            'pin_code': request.form.get('pin_code'),
            'city': request.form.get('city'),
            'state': request.form.get('state'),
            'pan_number': request.form.get('pan_number'),
            'aadhar_number': request.form.get('aadhar_number'),
            'itr': request.form.get('itr'),
            'cibil_score': request.form.get('cibil_score'),
            'job_or_business': request.form.get('job_or_business'),
            # Safe job/business handling
            'job_type': request.form.get('job_type') if request.form.get('job_or_business') == 'job' else None,
            'employment_type': request.form.get('employment_type') if request.form.get('job_or_business') == 'job' else None,
            'company_name': request.form.get('company_name') if request.form.get('job_or_business') == 'job' else None,
            'designation': request.form.get('designation') if request.form.get('job_or_business') == 'job' else None,
            'total_experience': request.form.get('total_experience') if request.form.get('job_or_business') == 'job' else None,
            'current_company_experience': request.form.get('current_company_experience') if request.form.get('job_or_business') == 'job' else None,
            'salary_mode': request.form.get('salary_mode') if request.form.get('job_or_business') == 'job' else None,
            'monthly_salary': request.form.get('monthly_salary') if request.form.get('job_or_business') == 'job' else None,
            'other_income': request.form.get('other_income') if request.form.get('job_or_business') == 'job' else None,
            'business_turnover': request.form.get('business_turnover') if request.form.get('job_or_business') == 'business' else None,
            'business_designation': request.form.get('business_designation') if request.form.get('job_or_business') == 'business' else None
        }

        try:
            supabase.table('users').insert(payload).execute()
        except Exception as e:
            app.logger.error('Supabase insert failed: %s', e)
            flash('Error saving profile', 'danger')
            return redirect(url_for('complete_profile_user'))

        session.pop('basic_profile', None)
        flash('Profile created — please login', 'success')
        return redirect(url_for('login'))

    return render_template('complete_profile_user.html', data=data)


@app.route('/profile/agent', methods=['GET', 'POST'])
def complete_profile_agent():
    data = session.get('basic_profile')
    if not data or data.get('user_type') != 'agent':
        flash('Start registration first.', 'warning')
        return redirect(url_for('index'))

    if request.method == 'POST':
        payload = {
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'mobile': data['mobile'],
            'password_hash': data['password'],
            'email': data['email'],
            'agent_type': request.form.get('agent_type'),
            'dsa_code': request.form.get('dsa_code'),
            'bank_name': request.form.get('bank_name'),
            'branch': request.form.get('branch'),
            'bank_finance_name': request.form.get('bank_finance_name'),
            'bank_finance_branch': request.form.get('bank_finance_branch'),
            'designation': request.form.get('designation'),
            'firm_name': request.form.get('firm_name'),
            'gst_number': request.form.get('gst_number'),
            'firm_address': request.form.get('firm_address'),
            'pin_code': request.form.get('pin_code'),
            'city': request.form.get('city'),
            'state': request.form.get('state')
        }
        try:
            supabase.table('agents').insert(payload).execute()
        except Exception as e:
            app.logger.error('Supabase insert failed: %s', e)
            flash('Error saving profile', 'danger')
            return redirect(url_for('complete_profile_agent'))

        session.pop('basic_profile', None)
        flash('Agent profile created — please login', 'success')
        return redirect(url_for('login'))

    return render_template('complete_profile_agent.html', data=data)


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        password = request.form.get('password')

        # Search users then agents then admins
        for table, role in [('users','user'), ('agents','agent')]:
            try:
                res = supabase.table(table).select('*').eq('email', identifier).execute()
                row = res.data[0] if res.data else None
                if not row:
                    res = supabase.table(table).select('*').eq('mobile', identifier).execute()
                    row = res.data[0] if res.data else None
                if row:
                    # NOTE: this assumes you store plain password column (change to hashed in prod)
                    if row.get('password') and row.get('password') == password:
                        session['user'] = {
                            'id': row.get('id'),
                            'first_name': row.get('first_name'),
                            'role': role,
                            'email': row.get('email')
                        }
                        flash('Logged in', 'success')
                        if role == 'user':
                            return redirect(url_for('dashboard_user'))
                        return redirect(url_for('dashboard_agent'))
                    else:
                        flash('Invalid credentials', 'danger')
                        return redirect(url_for('login'))
            except Exception:
                continue
        flash('User not found', 'warning')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard/user')
@login_required(role='user')
def dashboard_user():
    # fetch user loans
    user_mobile = session['user']['mobile']
    loans = supabase.table('loan_requests').select('*').eq('user_mobile', user_mobile).execute().data or []
    return render_template('dashboard_user.html', loans=loans)

@app.route('/dashboard/agent')
@login_required(role='agent')
def dashboard_agent():
    # agent view: show pending loans (simple)
    loans = supabase.table('loan_requests').select('*').eq('status','Pending').execute().data or []
    return render_template('dashboard_agent.html', loans=loans)

# Loan request
@app.route('/loan-request', methods=['GET','POST'])
@login_required(role='user')
def loan_request_route():
    if request.method == 'POST':
        # Generate unique loan_id
        try:
            res = supabase.table('loan_requests').select('loan_id').order('created_at', desc=True).limit(1).execute()
            last_loan = res.data[0] if res.data else None
            if last_loan and last_loan.get('loan_id'):
                last_num = int(last_loan['loan_id'].replace('LSH',''))
                new_num = last_num + 1
            else:
                new_num = 1
            loan_id = f"LSH{str(new_num).zfill(4)}"
        except Exception as e:
            app.logger.error("Loan ID generation failed: %s", e)
            loan_id = "LSH0001"

        payload = {
            'loan_id': loan_id,
            'user_mobile': session['user']['mobile'],  # user identification by mobile
            'loan_type': request.form.get('loan_type'),
            'amount': request.form.get('amount'),
            'duration': request.form.get('duration'),
            'reason': request.form.get('reason'),
            'status': 'Pending'
        }

        try:
            supabase.table('loan_requests').insert(payload).execute()
            flash(f'Loan requested successfully. Your Loan ID is {loan_id}', 'success')
        except Exception as e:
            app.logger.error("Loan request insert failed: %s", e)
            flash('Error requesting loan', 'danger')

        return redirect(url_for('dashboard_user'))
    return render_template('loan_request.html')

def generate_loan_pdf(loan):
    """
    loan: dict with loan details + user info
    returns BytesIO of PDF
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    x = 40
    y = height - 60
    p.setFont("Helvetica-Bold", 16)
    p.drawString(x, y, "Loan Profile - LoanSaathiHub")
    y -= 30
    p.setFont("Helvetica", 11)
    p.drawString(x, y, f"Loan ID: {loan.get('id') or loan.get('loan_id')}")
    y -= 20
    p.drawString(x, y, f"Loan Type: {loan.get('loan_type')}")
    y -= 20
    p.drawString(x, y, f"Amount: {loan.get('amount')}")
    y -= 20
    p.drawString(x, y, f"Duration (months): {loan.get('duration')}")
    y -= 30

    # user info if present
    user = loan.get('user') or {}
    p.setFont("Helvetica-Bold", 12)
    p.drawString(x, y, "Applicant Details:")
    y -= 20
    p.setFont("Helvetica", 11)
    p.drawString(x, y, f"Name: {user.get('first_name','') } {user.get('last_name','')}")
    y -= 18
    p.drawString(x, y, f"Email: {user.get('email','')}")
    y -= 18
    p.drawString(x, y, f"Mobile: {user.get('mobile','')}")
    y -= 18
    p.drawString(x, y, f"Address: {user.get('address1','')} {user.get('address2','')}, {user.get('city','')} - {user.get('pin_code','')}")
    y -= 30

    p.setFont("Helvetica-Oblique", 9)
    p.drawString(x, y, f"Generated by LoanSaathiHub on {str(datetime.utcnow())[:19]} UTC")
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

@app.route('/loan/<loan_id>/pdf')
@login_required(role='agent')
def loan_pdf(loan_id):
    # fetch loan and user
    loan_res = supabase.table('loan_requests').select('*').eq('id', loan_id).single().execute()
    loan = loan_res.data
    if not loan:
        flash('Loan not found', 'danger')
        return redirect(url_for('dashboard_agent'))
    # fetch user record
    user_res = supabase.table('users').select('*').eq('id', loan.get('user_id')).single().execute()
    loan['user'] = user_res.data if user_res and user_res.data else {}
    pdf_buffer = generate_loan_pdf(loan)
    # mark loan as Active if not already (agent opened profile)
    try:
        supabase.table('loan_requests').update({'status':'Active'}).eq('id', loan_id).execute()
    except Exception:
        pass
    return send_file(pdf_buffer, as_attachment=False, download_name=f"loan_{loan_id}.pdf", mimetype='application/pdf')

@app.route('/purchase/<loan_id>', methods=['GET','POST'])
@login_required(role='agent')
def purchase_lead(loan_id):
    # display payment page
    loan_res = supabase.table('loan_requests').select('*').eq('id', loan_id).single().execute()
    loan = loan_res.data
    if not loan:
        flash('Loan not found', 'danger')
        return redirect(url_for('dashboard_agent'))

    amount = 99.00  # INR 99
    if request.method == 'POST':
        provider = request.form.get('provider','mock')
        # create payment row pending
        payment_payload = {
            'loan_request_id': loan_id,
            'agent_email': session['user']['email'],
            'amount': decimal.Decimal(str(amount)),
            'provider': provider,
            'status': 'pending'
        }
        pay_res = supabase.table('payments').insert(payment_payload).execute()
        payment_row = pay_res.data[0] if pay_res and pay_res.data else None

        if provider == 'razorpay' and razorpay_client:
            # create razorpay order
            order = razorpay_client.order.create(dict(amount=int(amount*100), currency='INR', receipt=str(payment_row.get('id'))))
            # pass order id to template to complete checkout in frontend (Razorpay checkout)
            return render_template('payment.html', loan=loan, provider='razorpay', order=order, amount=amount)
        else:
            # mock success: update payment and loan status
            supabase.table('payments').update({'status':'success', 'provider_payment_id': 'MOCK123'}).eq('id', payment_row['id']).execute()
            supabase.table('loan_requests').update({'status':'Approved'}).eq('id', loan_id).execute()
            flash('Payment successful (mock). Lead unlocked.', 'success')
            return redirect(url_for('dashboard_agent'))

    return render_template('purchase.html', loan=loan, amount=amount)

def generate_pdf_for_loan(loan, full=False):
    """
    loan: dict from loan_requests containing user info (we try to fetch user by user_id)
    full: if False => hide mobile, email, address; if True => show all
    returns bytes
    """
    # fetch user info
    user = None
    try:
        user_res = supabase.table("users").select("*").eq("mobile", loan.get("user_mobile")).single().execute()
        user = user_res.data if user_res and user_res.data else {}
    except Exception:
        user = {}

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, "LoanSaathiHub - Lead Details", ln=True, align="C")
    pdf.ln(4)
    pdf.set_font("Arial", size=11)
    pdf.cell(50, 8, "Loan ID:", ln=0)
    pdf.cell(0, 8, str(loan.get("id") or loan.get("loan_id", "")), ln=True)

    pdf.cell(50, 8, "Loan Type:", ln=0)
    pdf.cell(0, 8, str(loan.get("loan_type", "")), ln=True)

    pdf.cell(50, 8, "Amount:", ln=0)
    pdf.cell(0, 8, str(loan.get("amount", "")), ln=True)

    pdf.cell(50, 8, "Duration (months):", ln=0)
    pdf.cell(0, 8, str(loan.get("duration", "")), ln=True)
    pdf.ln(6)

    pdf.cell(0, 8, "Applicant Details:", ln=True)
    pdf.ln(2)

    pdf.cell(50, 8, "Name:", ln=0)
    pdf.cell(0, 8, f"{user.get('first_name','')} {user.get('last_name','')}", ln=True)

    # Contact fields: hide if partial
    if full:
        pdf.cell(50, 8, "Mobile:", ln=0)
        pdf.cell(0, 8, user.get('mobile', 'N/A'), ln=True)

        pdf.cell(50, 8, "Email:", ln=0)
        pdf.cell(0, 8, user.get('email', 'N/A'), ln=True)

        pdf.cell(50, 8, "Address:", ln=0)
        addr = ", ".join(filter(None, [user.get('address1'), user.get('address2'), user.get('city'), user.get('state'), user.get('pin_code')]))
        pdf.multi_cell(0, 6, addr or "N/A")
    else:
        pdf.cell(50, 8, "Mobile:", ln=0)
        pdf.cell(0, 8, "****", ln=True)

        pdf.cell(50, 8, "Email:", ln=0)
        pdf.cell(0, 8, "****", ln=True)

        pdf.cell(50, 8, "Address:", ln=0)
        pdf.cell(0, 8, "****", ln=True)

    pdf.ln(6)
    pdf.cell(0, 8, "Note: This is a generated PDF from LoanSaathiHub", ln=True)
    # Return bytes
    out = pdf.output(dest='S').encode('latin-1')
    return out

@app.route('/agent/leads')
@login_required(role='agent')
def agent_leads():
    # list leads (Pending/Active etc.)
    try:
        loans_res = supabase.table("loan_requests").select("*").order("created_at", desc=True).execute()
        loans = loans_res.data if loans_res and loans_res.data else []
    except Exception as e:
        app.logger.error("Error fetching leads: %s", e)
        loans = []

    # fetch payments for this agent to know what is purchased
    agent_email = session['user'].get('email')
    try:
        payments_res = supabase.table("payments").select("*").eq("agent_email", agent_email).execute()
        payments = payments_res.data if payments_res and payments_res.data else []
        purchased_loan_ids = {p.get('loan_id') for p in payments}
    except Exception:
        purchased_loan_ids = set()

    return render_template('agent_leads.html', loans=loans, purchased_loan_ids=purchased_loan_ids)

@app.route('/loan/<loan_id>/partial-pdf')
@login_required(role='agent')
def partial_pdf(loan_id):
    try:
        user_res = supabase.table('users').select('*').eq('mobile', loan.get('user_mobile')).single().execute()
        loan = res.data if res and res.data else None
    except Exception as e:
        app.logger.error("Error fetching loan: %s", e)
        loan = None

    if not loan:
        flash("Lead not found", "error")
        return redirect(url_for('agent_leads'))

    pdf_bytes = generate_pdf_for_loan(loan, full=False)
    return send_file(io.BytesIO(pdf_bytes), download_name=f"lead_{loan_id}_partial.pdf", as_attachment=True, mimetype='application/pdf')

@app.route('/loan/<loan_id>/buy', methods=['GET','POST'])
@login_required(role='agent')
def buy_lead(loan_id):
    # Simple mock payment: GET shows details + Pay button, POST simulates successful payment
    try:
        res = supabase.table("loan_requests").select("*").eq("id", loan_id).single().execute()
        loan = res.data if res and res.data else None
    except Exception as e:
        app.logger.error("Error fetching loan: %s", e)
        loan = None

    if not loan:
        flash("Lead not found", "error")
        return redirect(url_for('agent_leads'))

    if request.method == 'POST':
        # create payment record
        payment_payload = {
            "loan_id": loan_id,
            "agent_email": session['user'].get('email'),
            "amount": 99.0,  # fixed price
            "currency": "INR",
            "status": "success",
            "paid_at": datetime.utcnow().isoformat()
        }
        try:
            supabase.table("payments").insert(payment_payload).execute()
        except Exception as e:
            app.logger.error("Error recording payment: %s", e)
            flash("Payment failed to be recorded", "danger")
            return redirect(url_for('agent_leads'))

        flash("Payment successful — full lead unlocked", "success")
        return redirect(url_for('download_full_pdf', loan_id=loan_id))

    return render_template('buy_lead.html', loan=loan)

@app.route('/loan/<loan_id>/full-pdf')
@login_required(role='agent')
def download_full_pdf(loan_id):
    # check payment exists
    agent_email = session['user'].get('email')
    try:
        pay_res = supabase.table("payments").select("*").eq("loan_id", loan_id).eq("agent_email", agent_email).execute()
        paid = bool(pay_res and pay_res.data)
    except Exception as e:
        app.logger.error("Payment check error: %s", e)
        paid = False

    if not paid:
        flash("You must purchase the lead to download full details.", "warning")
        return redirect(url_for('buy_lead', loan_id=loan_id))

    try:
        res = supabase.table("loan_requests").select("*").eq("id", loan_id).single().execute()
        loan = res.data if res and res.data else None
    except Exception as e:
        app.logger.error("Error fetching loan: %s", e)
        loan = None

    if not loan:
        flash("Lead not found", "error")
        return redirect(url_for('agent_leads'))

    pdf_bytes = generate_pdf_for_loan(loan, full=True)
    return send_file(io.BytesIO(pdf_bytes), download_name=f"lead_{loan_id}_full.pdf", as_attachment=True, mimetype='application/pdf')

@app.context_processor
def inject_user():
    return dict(user=session.get('user'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
