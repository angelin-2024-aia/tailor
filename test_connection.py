#!/usr/bin/env python
import sqlite3
import os

DB_PATH = 'tailor_pro.db'

print(f"[TEST] Connecting to {DB_PATH}...")
try:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    print("[OK] Connected to SQLite")
    
    cur = conn.cursor()
    
    # Test query
    print("[TEST] Running SELECT COUNT(*) FROM customers...")
    cur.execute("SELECT COUNT(*) as count FROM customers")
    row = cur.fetchone()
    print(f"[OK] Query result: {dict(row) if row else None}")
    
    # Test with data
    print("[TEST] Inserting test customer...")
    cur.execute("INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)",
                ("Test Customer", "9876543210", "Test Address"))
    conn.commit()
    print("[OK] Insert successful")
    
    # Test count again
    cur.execute("SELECT COUNT(*) as count FROM customers")
    count = dict(cur.fetchone())['count']
    print(f"[OK] Customer count: {count}")
    
    conn.close()
    print("[SUCCESS] All tests passed!")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
