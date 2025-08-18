# main/supabase_client.py
import os
from supabase import create_client

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip()
SUPABASE_KEY = (os.getenv("SUPABASE_KEY") or "").strip()

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print("⚠️ Supabase client init failed:", e)
        supabase = None
else:
    print("ℹ️ Supabase env not set; skipping client init")
