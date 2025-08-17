import psycopg2
import os

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="_Mayuri%4096621%23sunny_",   # ya encoded version डालो
    host="db.vdnbasxyyyeqpxtprpav.supabase.co",
    port="5432",
    sslmode="require"
)

print("✅ Connected successfully")
conn.close()
