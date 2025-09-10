from supabase import create_client, Client
from django.conf import settings
import os
from dotenv import load_dotenv

# Load environment variables (local .env)
load_dotenv()

# ------------------------
# Supabase Config (safe fallbacks to Django settings)
# ------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL") or getattr(settings, "SUPABASE_URL", None)
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY") or getattr(settings, "SUPABASE_ANON_KEY", None)
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None)

# Validate presence
if not SUPABASE_URL:
    print("⚠️ SUPABASE_URL not configured. Supabase features will be disabled.")
if not SUPABASE_ANON_KEY:
    print("⚠️ SUPABASE_ANON_KEY not configured. Public client will be disabled.")
if not SUPABASE_SERVICE_ROLE_KEY:
    print("⚠️ SUPABASE_SERVICE_ROLE_KEY not configured. Admin client will be disabled.")

# Default clients (may be None if keys missing)
supabase: Client | None = None
supabase_admin: Client | None = None

try:
    if SUPABASE_URL and SUPABASE_ANON_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
except Exception as e:
    print("❌ Failed to create Supabase public client:", e)
    supabase = None

try:
    if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
        supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
except Exception as e:
    print("❌ Failed to create Supabase admin client:", e)
    supabase_admin = None


# ------------------------
# CLIENT HELPERS
# ------------------------
def _make_client(key: str) -> Client | None:
    """Return a Supabase client with a specific key (or None if not possible)"""
    if not SUPABASE_URL or not key:
        print("⚠️ _make_client: missing URL or key")
        return None
    try:
        return create_client(SUPABASE_URL, key)
    except Exception as e:
        print("❌ _make_client error:", e)
        return None


def supabase_public() -> Client | None:
    """Anon (public) client"""
    return _make_client(SUPABASE_ANON_KEY) if SUPABASE_ANON_KEY else supabase


def supabase_admin_client() -> Client | None:
    """Admin client – full access, use only server-side"""
    return supabase_admin


def supabase_as_user(access_token: str, refresh_token: str | None = None) -> Client | None:
    """Client acting as a logged-in user. Attempts to set user's session on anon client."""
    client = supabase_public()
    if client is None:
        print("⚠️ supabase_as_user: public client not available")
        return None
    try:
        # Attempt to set session (implementation may vary by supabase client version)
        if hasattr(client.auth, "set_session"):
            client.auth.set_session(access_token, refresh_token)
        elif hasattr(client.auth, "session"):
            # older/newer clients may expose different APIs
            client.auth.session = {"access_token": access_token, "refresh_token": refresh_token}
        else:
            print("⚠️ supabase_as_user: unable to set session - unknown client.auth API")
        return client
    except Exception as e:
        print("❌ supabase_as_user error:", e)
        return None


# ------------------------
# SYNC / UPSERT HELPERS
# ------------------------
def create_user_in_supabase(user_id, auth_user_id, email, role):
    """Insert new user into Supabase `main_user` table using ADMIN client"""
    if supabase_admin is None:
        print("⚠️ create_user_in_supabase: admin client not available")
        return None
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
    Field names mapped to common snake_case keys — adjust to your Supabase schema if needed.
    """
    if supabase_admin is None:
        print("⚠️ upsert_profile_in_supabase: admin client not available")
        return None

    try:
        profile_data = {
            "user_id": str(user.id),
            "email": user.email,
            "role": getattr(user, "role", None),
            "full_name": getattr(profile, "full_name", None),
            "mobile": getattr(profile, "mobile", None),
            "gender": getattr(profile, "gender", None),
            "marital_status": getattr(profile, "marital_status", None),
            "address": getattr(profile, "address", None),
            "pincode": getattr(profile, "pincode", None),
            "city": getattr(profile, "city", None),
            "state": getattr(profile, "state", None),
            # Use field names that match your Django models (views used pancard_number / aadhaar_number)
            "pancard_number": getattr(profile, "pancard_number", None),
            "aadhaar_number": getattr(profile, "aadhaar_number", None),
        }

        if getattr(user, "role", None) == "applicant":
            profile_data.update({
                "employment_type": getattr(details, "employment_type", None),
                "cibil_score": getattr(details, "cibil_score", None),
                "company_name": getattr(details, "company_name", None),
                "company_type": getattr(details, "company_type", None),
                "designation": getattr(details, "designation", None),
                "itr": getattr(details, "itr", None),
                "current_salary": getattr(details, "current_salary", None),
                "other_income": getattr(details, "other_income", None),
                "total_emi_job": getattr(details, "total_emi", None),
                "business_name": getattr(details, "business_name", None),
                "business_type": getattr(details, "business_type", None),
                "business_sector": getattr(details, "business_sector", None),
                "total_turnover": getattr(details, "total_turnover", None),
                "last_year_turnover": getattr(details, "last_year_turnover", None),
                "total_emi_business": getattr(details, "business_total_emi", None),
                "business_itr_status": getattr(details, "business_itr_status", None),
            })

        elif getattr(user, "role", None) == "lender":
            profile_data.update({
                "lender_type": getattr(details, "lender_type", None),
                "dsa_code": getattr(details, "dsa_code", None),
                "firm_name": getattr(details, "bank_firm_name", None) or getattr(details, "firm_name", None),
                "gst_number": getattr(details, "gst_number", None),
                "branch_name": getattr(details, "branch_name", None),
            })

        res = supabase_admin.table("main_profile").upsert(profile_data).execute()
        print("✅ Supabase profile upsert:", res)
        return res
    except Exception as e:
        print("❌ Supabase profile upsert failed:", e)
        return None


def sync_loan_request_to_supabase(loan):
    """Sync loan request into Supabase `main_loanrequest`"""
    if supabase_admin is None:
        print("⚠️ sync_loan_request_to_supabase: admin client not available")
        return None
    try:
        data = {
            "loan_id": getattr(loan, "loan_id", None),
            "applicant_id": str(getattr(loan.applicant, "id", None)) if getattr(loan, "applicant", None) else None,
            "loan_type": getattr(loan, "loan_type", None),
            "amount_requested": getattr(loan, "amount_requested", None),
            "duration_months": getattr(loan, "duration_months", None),
            "interest_rate": getattr(loan, "interest_rate", None),
            # use reason_for_loan if present, else remarks/description
            "reason_for_loan": getattr(loan, "reason_for_loan", None) or getattr(loan, "remarks", None),
            "status": getattr(loan, "status", None),
        }
        res = supabase_admin.table("main_loanrequest").insert(data).execute()
        print("✅ Loan request synced:", res)
        return res
    except Exception as e:
        print("❌ Loan request sync failed:", e)
        return None


def sync_payment_to_supabase(payment):
    """Sync payment into Supabase `main_payment`"""
    if supabase_admin is None:
        print("⚠️ sync_payment_to_supabase: admin client not available")
        return None
    try:
        data = {
            "lender_id": str(getattr(payment.lender, "id", None)) if getattr(payment, "lender", None) else None,
            "loan_request_id": str(getattr(payment.loan_request, "id", None)) if getattr(payment, "loan_request", None) else None,
            "payment_method": getattr(payment, "payment_method", None),
            "amount": getattr(payment, "amount", None),
            "status": getattr(payment, "status", None),
            "created_at": getattr(payment, "created_at", None),
        }
        res = supabase_admin.table("main_payment").insert(data).execute()
        print("✅ Payment synced:", res)
        return res
    except Exception as e:
        print("❌ Payment sync failed:", e)
        return None
