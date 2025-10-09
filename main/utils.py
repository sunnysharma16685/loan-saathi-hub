import os
import random
import logging
import warnings
from django.conf import settings
from django.core.mail import send_mail
from dotenv import load_dotenv
import razorpay

# -------------------- ENV + LOGGER SETUP --------------------
load_dotenv()
logger = logging.getLogger(__name__)

# Silence noisy pkg_resources warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

# -------------------- RAZORPAY CLIENT CONFIG --------------------

def get_razorpay_client():
    """
    Return a configured Razorpay client.
    This replaces the old PhonePe SDK client.
    """
    try:
        key_id = os.getenv("RAZORPAY_KEY_ID", getattr(settings, "RAZORPAY_KEY_ID", ""))
        key_secret = os.getenv("RAZORPAY_KEY_SECRET", getattr(settings, "RAZORPAY_KEY_SECRET", ""))
        if not key_id or not key_secret:
            raise ValueError("Missing Razorpay API credentials.")
        client = razorpay.Client(auth=(key_id, key_secret))
        logger.info("✅ Razorpay client initialized successfully.")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to initialize Razorpay client: {e}")
        return None


# -------------------- EMAIL OTP SERVICE --------------------

def send_email_otp(email: str) -> dict:
    """
    Send a 6-digit OTP to the given email.
    Returns dict:
        { "ok": True, "otp": "123456" }  ✅ success
        { "ok": False, "error": "reason" } ❌ failure
    """
    try:
        otp = str(random.randint(100000, 999999))
        subject = "Loan Saathi Hub OTP Verification"
        message = f"Your OTP for Loan Saathi Hub is {otp}. It will expire in 5 minutes."

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        logger.info(f"✅ OTP {otp} sent successfully to {email}")
        return {"ok": True, "otp": otp}

    except Exception as e:
        logger.error(f"❌ OTP sending failed to {email}: {e}")
        return {"ok": False, "error": str(e)}


# -------------------- ID GENERATORS --------------------
# You can safely keep these as-is, even without Supabase.

def generate_applicant_id():
    """Generate unique Applicant ID like LSHA0001"""
    try:
        response = supabase.table("applicants").select("id").order("created_at", desc=True).limit(1).execute()
        if response.data:
            last_id = response.data[0]["id"]
            num = int(last_id.replace("LSHA", ""))
            return f"LSHA{num + 1:04d}"
        return "LSHA0001"
    except Exception as e:
        logger.warning(f"⚠️ Applicant ID generation fallback: {e}")
        return f"LSHA{random.randint(1000, 9999)}"


def generate_lender_id():
    """Generate unique Lender ID like LSHL0001"""
    try:
        response = supabase.table("lenders").select("id").order("created_at", desc=True).limit(1).execute()
        if response.data:
            last_id = response.data[0]["id"]
            num = int(last_id.replace("LSHL", ""))
            return f"LSHL{num + 1:04d}"
        return "LSHL0001"
    except Exception as e:
        logger.warning(f"⚠️ Lender ID generation fallback: {e}")
        return f"LSHL{random.randint(1000, 9999)}"


def generate_admin_id():
    """Generate unique Admin ID like LSHAD0001"""
    try:
        response = supabase.table("admins").select("id").order("created_at", desc=True).limit(1).execute()
        if response.data:
            last_id = response.data[0]["id"]
            num = int(last_id.replace("LSHAD", ""))
            return f"LSHAD{num + 1:04d}"
        return "LSHAD0001"
    except Exception as e:
        logger.warning(f"⚠️ Admin ID generation fallback: {e}")
        return f"LSHAD{random.randint(1000, 9999)}"


def generate_loan_id():
    """Generate unique Loan ID like LSH0001"""
    try:
        response = supabase.table("loans").select("loan_id").order("created_at", desc=True).limit(1).execute()
        if response.data:
            last_id = response.data[0]["loan_id"]
            num = int(last_id.replace("LSH", ""))
            return f"LSH{num + 1:04d}"
        return "LSH0001"
    except Exception as e:
        logger.warning(f"⚠️ Loan ID generation fallback: {e}")
        return f"LSH{random.randint(1000, 9999)}"
