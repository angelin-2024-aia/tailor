"""
Quick local DB connection tester. Fill DATABASE_URL or set env var and run:

Windows PowerShell example:
$env:DATABASE_URL = "postgresql://postgres:NEWPASS@db.pbjnkefaueedsgxdxddo.supabase.co:5432/postgres?sslmode=require"
python test_db.py
"""
import os
import sys
import psycopg

url = os.environ.get('DATABASE_URL')
if not url:
    print('Set DATABASE_URL environment variable first.')
    sys.exit(1)

try:
    conn = psycopg.connect(url, connect_timeout=5)
    print('Connected successfully')
    print('Server params:', conn.info.dsn_parameters)
    conn.close()
except Exception as e:
    print('Connection failed:')
    print(e)
    sys.exit(2)
