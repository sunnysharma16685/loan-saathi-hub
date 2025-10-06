import random
import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

# -------------------- EMAIL OTP SERVICE --------------------

def send_email_otp(email: str) -> dict:
    """
    Send a 6-digit OTP to the given email.
    Returns dict:
        { "ok": True, "otp": "123456" }  ✅ success
        { "ok": False, "error": "reason" } ❌ failure
    """
    try:
        otp = str(random.randint(100000, 999999))  # ✅ Generate 6-digit OTP

        subject = "Loan Saathi Hub OTP Verification"
        message = f"Your OTP for Loan Saathi Hub is {otp}. It will expire in 5 minutes."

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,  # Raise error if fails
        )

        logger.info(f"✅ OTP {otp} sent successfully to {email}")
        return {"ok": True, "otp": otp}

    except Exception as e:
        logger.error(f"❌ OTP sending failed to {email}: {e}")
        return {"ok": False, "error": str(e)}


# -------------------- ID GENERATORS --------------------

def generate_applicant_id():
    """Generate unique Applicant ID like LSHA0001"""
    response = supabase.table("applicants").select("id").order("created_at", desc=True).limit(1).execute()
    if response.data:
        last_id = response.data[0]["id"]
        num = int(last_id.replace("LSHA", ""))
        return f"LSHA{num+1:04d}"
    return "LSHA0001"


def generate_lender_id():
    """Generate unique Lender ID like LSHL0001"""
    response = supabase.table("lenders").select("id").order("created_at", desc=True).limit(1).execute()
    if response.data:
        last_id = response.data[0]["id"]
        num = int(last_id.replace("LSHL", ""))
        return f"LSHL{num+1:04d}"
    return "LSHL0001"


def generate_admin_id():
    """Generate unique Admin ID like LSHAD0001"""
    response = supabase.table("admins").select("id").order("created_at", desc=True).limit(1).execute()
    if response.data:
        last_id = response.data[0]["id"]
        num = int(last_id.replace("LSHAD", ""))
        return f"LSHAD{num+1:04d}"
    return "LSHAD0001"


def generate_loan_id():
    """Generate unique Loan ID like LSH0001"""
    response = supabase.table("loans").select("loan_id").order("created_at", desc=True).limit(1).execute()
    if response.data:
        last_id = response.data[0]["loan_id"]
        num = int(last_id.replace("LSH", ""))
        return f"LSH{num+1:04d}"
    return "LSH0001"
