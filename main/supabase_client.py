from supabase import create_client, Client
from django.conf import settings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ------------------------
# Supabase Config
# ------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", settings.SUPABASE_URL)
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", settings.SUPABASE_ANON_KEY)
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", settings.SUPABASE_SERVICE_ROLE_KEY)

# Default clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)          # anon
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)  # service role

# ------------------------
# CLIENT HELPERS
# ------------------------
def _make_client(key: str) -> Client:
    """Return a Supabase client with a specific key"""
    return create_client(SUPABASE_URL, key)


def supabase_public() -> Client:
    """Anon (public) client"""
    return _make_client(SUPABASE_ANON_KEY)


def supabase_admin_client() -> Client:
    """Admin client – full access, use only server-side"""
    return supabase_admin


def supabase_as_user(access_token: str, refresh_token: str | None = None) -> Client:
    """Client acting as a logged-in user"""
    client = supabase_public()
    client.auth.set_session(access_token, refresh_token)
    return client


# ------------------------
# SYNC / UPSERT HELPERS
# ------------------------
def create_user_in_supabase(user_id, auth_user_id, email, role):
    """Insert new user into Supabase `main_user` table using ADMIN client"""
    try:
        data = {
            "id": str(user_id),
            "supabase_uid": str(auth_user_id),
            "email": email,
            "role": role,
        }
        res = supabase_admin.table("main_user").insert(data).execute()
        print("✅ Supabase user created:", res)
        return res
    except Exception as e:
        print("❌ Supabase user creation failed:", e)
        return None


def upsert_profile_in_supabase(user, profile, details):
    """
    Upsert profile + applicant/lender details into Supabase `main_profile`
    """
    try:
        profile_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "full_name": profile.full_name,
            "mobile": profile.mobile,
            "gender": profile.gender,
            "marital_status": profile.marital_status,
            "address": profile.address,
            "pincode": profile.pincode,
            "city": profile.city,
            "state": profile.state,
            "pan_number": profile.pan_number,
            "aadhar_number": profile.aadhar_number,
        }

        if user.role == "applicant":
            profile_data.update({
                "cibil_score": details.cibil_score,
                "company_name": details.company_name,
                "company_type": details.company_type,
                "designation": details.designation,
                "itr_job": details.itr_job,
                "current_salary": details.current_salary,
                "other_income": details.other_income,
                "total_emi_job": details.total_emi,
                "business_name": details.business_name,
                "business_type": details.business_type,
                "business_sector": details.business_sector,
                "turnover_3y": details.turnover_3y,
                "turnover_1y": details.turnover_1y,
                "total_emi_business": details.total_emi,
                "itr_business": details.itr_business,
            })

        elif user.role == "lender":
            profile_data.update({
                "lender_type": details.lender_type,
                "dsa_code": details.dsa_code,
                "firm_name": details.firm_name,
                "gst_number": details.gst_number,
                "branch_name": details.branch_name,
            })

        res = supabase_admin.table("main_profile").upsert(profile_data).execute()
        print("✅ Supabase profile upsert:", res)
        return res
    except Exception as e:
        print("❌ Supabase profile upsert failed:", e)
        return None


def sync_loan_request_to_supabase(loan):
    """Sync loan request into Supabase `main_loanrequest`"""
    try:
        data = {
            "loan_id": loan.loan_id,
            "applicant_id": str(loan.applicant.id),
            "loan_type": loan.loan_type,
            "amount_requested": loan.amount_requested,
            "duration_months": loan.duration_months,
            "interest_rate": loan.interest_rate,
            "remarks": loan.remarks,
        }
        res = supabase_admin.table("main_loanrequest").insert(data).execute()
        print("✅ Loan request synced:", res)
        return res
    except Exception as e:
        print("❌ Loan request sync failed:", e)
        return None


def sync_payment_to_supabase(payment):
    """Sync payment into Supabase `main_payment`"""
    try:
        data = {
            "lender_id": str(payment.lender.id),
            "loan_request_id": str(payment.loan_request.id),
            "payment_method": payment.payment_method,
            "amount": payment.amount,
            "status": payment.status,
        }
        res = supabase_admin.table("main_payment").insert(data).execute()
        print("✅ Payment synced:", res)
        return res
    except Exception as e:
        print("❌ Payment sync failed:", e)
        return None
