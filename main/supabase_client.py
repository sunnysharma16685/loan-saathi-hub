from supabase import create_client, Client
from django.conf import settings
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Supabase Config ---
SUPABASE_URL = os.getenv("SUPABASE_URL", settings.SUPABASE_URL)
SUPABASE_KEY = os.getenv("SUPABASE_KEY", settings.SUPABASE_ANON_KEY)

# Default client (anon)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ------------------------
# CLIENT HELPERS
# ------------------------
def _make_client(key: str) -> Client:
    return create_client(settings.SUPABASE_URL, key)


def supabase_public() -> Client:
    return _make_client(settings.SUPABASE_ANON_KEY)


def supabase_admin() -> Client:
    """Full access – use only on server side."""
    return _make_client(settings.SUPABASE_SERVICE_ROLE_KEY)


def supabase_as_user(access_token: str, refresh_token: str | None = None) -> Client:
    client = supabase_public()
    client.auth.set_session(access_token, refresh_token)
    return client


# ------------------------
# SYNC HELPERS
# ------------------------
def create_user_in_supabase(user_id, auth_user_id, email, role):
    """Insert new user into Supabase `users` table"""
    try:
        data = {
            "id": str(user_id),
            "auth_user_id": auth_user_id,
            "email": email,
            "role": role,
        }
        res = supabase.table("users").insert(data).execute()
        print("✅ Supabase user created:", res)
        return res
    except Exception as e:
        print("❌ Supabase user creation failed:", e)
        return None


def upsert_profile_in_supabase(table, profile_data):
    """Upsert profile into Supabase (applicant_profiles / lender_profiles)"""
    try:
        res = supabase.table(table).upsert(profile_data).execute()
        print(f"✅ Supabase {table} upsert:", res)
        return res
    except Exception as e:
        print(f"❌ Supabase {table} upsert failed:", e)
        return None


def sync_loan_request_to_supabase(loan_data):
    """Sync loan requests into Supabase"""
    try:
        res = supabase.table("loan_requests").upsert(loan_data).execute()
        print("✅ Loan request synced:", res)
        return res
    except Exception as e:
        print("❌ Loan request sync failed:", e)
        return None


def sync_payment_to_supabase(payment_data):
    """Sync payments into Supabase"""
    try:
        res = supabase.table("payments").upsert(payment_data).execute()
        print("✅ Payment synced:", res)
        return res
    except Exception as e:
        print("❌ Payment sync failed:", e)
        return None
