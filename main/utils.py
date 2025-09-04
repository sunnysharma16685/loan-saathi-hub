from .supabase_client import supabase

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
