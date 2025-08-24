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
SUPABASE_KEY = os.getenv("SUPABASE_KEY", settings.SUPABASE_ANON_KEY)

# Default client (anon)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ------------------------
# CLIENT HELPERS
# ------------------------
def _make_client(key: str) -> Client:
    """Return a Supabase client with a specific key"""
    return create_client(settings.SUPABASE_URL, key)


def supabase_public() -> Client:
    """Public (anon) client"""
    return _make_client(settings.SUPABASE_ANON_KEY)


def supabase_admin() -> Client:
    """Admin client – full access, use only server-side"""
    return _make_client(settings.SUPABASE_SERVICE_ROLE_KEY)


def supabase_as_user(access_token: str, refresh_token: str | None = None) -> Client:
    """Client acting as a logged-in user"""
    client = supabase_public()
    client.auth.set_session(access_token, refresh_token)
    return client


# ------------------------
# SYNC / UPSERT HELPERS
# ------------------------
def create_user_in_supabase(user_id, auth_user_id, email, role):
    """Insert new user into Supabase `main_user` table"""
    try:
        data = {
            "id": str(user_id),
            "supabase_uid": str(auth_user_id),
            "email": email,
            "role": role,
        }
        res = supabase.table("main_user").insert(data).execute()
        print("✅ Supabase user created:", res)
        return res
    except Exception as e:
        print("❌ Supabase user creation failed:", e)
        return None


def upsert_profile_in_supabase(profile_data: dict):
    """Upsert profile into Supabase `main_profile`"""
    try:
        res = supabase.table("main_profile").upsert(profile_data).execute()
        print("✅ Supabase profile upsert:", res)
        return res
    except Exception as e:
        print("❌ Supabase profile upsert failed:", e)
        return None


def sync_loan_request_to_supabase(loan_data: dict):
    """Sync loan request into Supabase `main_loanrequest`"""
    try:
        res = supabase.table("main_loanrequest").insert({
            "loan_id": loan_data.get("loan_id"),
            "applicant_id": str(loan_data.get("applicant").id),
            "loan_type": loan_data.get("loan_type"),
            "amount_requested": loan_data.get("amount_requested"),
            "duration_months": loan_data.get("duration_months"),
            "interest_rate": loan_data.get("interest_rate"),
            "remarks": loan_data.get("remarks"),
        }).execute()
        print("✅ Loan request synced:", res)
        return res
    except Exception as e:
        print("❌ Loan request sync failed:", e)
        return None


def sync_payment_to_supabase(payment_data: dict):
    """Sync payment into Supabase `main_payment`"""
    try:
        res = supabase.table("main_payment").insert({
            "lender_id": str(payment_data.get("lender").id),
            "loan_request_id": str(payment_data.get("loan_request").id),
            "payment_method": payment_data.get("payment_method"),
            "amount": payment_data.get("amount"),
            "status": payment_data.get("status"),
        }).execute()
        print("✅ Payment synced:", res)
        return res
    except Exception as e:
        print("❌ Payment sync failed:", e)
        return None
