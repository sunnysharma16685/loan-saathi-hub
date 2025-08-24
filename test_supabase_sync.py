import uuid
from django.utils.crypto import get_random_string
from main.supabase_client import (
    create_user_in_supabase,
    upsert_profile_in_supabase,
    sync_loan_request_to_supabase,
    sync_payment_to_supabase
)

# ------------------------
# Dummy Test Data
# ------------------------
def run_test():
    print("🚀 Starting Supabase sync test...")

    # 1️⃣ Create dummy user
    user_id = uuid.uuid4()
    auth_user_id = uuid.uuid4()   # Supabase UID dummy
    email = f"test_{get_random_string(5)}@example.com"
    role = "applicant"

    print("\n👉 Creating user...")
    create_user_in_supabase(user_id, auth_user_id, email, role)

    # 2️⃣ Insert dummy profile
    profile_data = {
        "id": uuid.uuid4(),
        "user_id": str(user_id),
        "full_name": "Test User",
        "mobile": "9876543210",
        "gender": "Male",
        "marital_status": "Single",
        "address": "123 Test Street",
        "pincode": "400001",
        "city": "Mumbai",
        "state": "Maharashtra",
        "pan_number": "ABCDE1234F",
        "aadhaar": "123412341234",
    }

    print("\n👉 Upserting profile...")
    upsert_profile_in_supabase(profile_data)

    # 3️⃣ Insert dummy loan request
    loan_data = {
        "loan_id": "LSH" + get_random_string(4, allowed_chars="0123456789"),
        "applicant": type("Obj", (), {"id": user_id}),  # fake object with id
        "loan_type": "Personal Loan",
        "amount_requested": 500000,
        "duration_months": 24,
        "interest_rate": 12,
        "remarks": "Test loan request"
    }

    print("\n👉 Syncing loan request...")
    sync_loan_request_to_supabase(loan_data)

    # 4️⃣ Insert dummy payment
    payment_data = {
        "lender": type("Obj", (), {"id": uuid.uuid4()}),   # fake lender
        "loan_request": type("Obj", (), {"id": uuid.uuid4()}),  # fake loan
        "payment_method": "UPI",
        "amount": 1999,
        "status": "done"
    }

    print("\n👉 Syncing payment...")
    sync_payment_to_supabase(payment_data)

    print("\n✅ All test data pushed to Supabase!")


if __name__ == "__main__":
    run_test()
