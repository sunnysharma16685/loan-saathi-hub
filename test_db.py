import psycopg2

try:
    conn = psycopg2.connect(
        "postgresql://postgres:hnXW2t4etLwa1Kxu@db.vdnbasxyyyeqpxtprpav.supabase.co:5432/postgres"
    )
    print("✅ Connection successful!")
    conn.close()
except Exception as e:
    print("❌ Error:", e)
