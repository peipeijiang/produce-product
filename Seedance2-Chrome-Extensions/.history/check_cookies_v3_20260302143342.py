import sqlite3
import os

cookies_path = "playwright/user-data/Default/Cookies"

if not os.path.exists(cookies_path):
    print(f"Error: Cookies file not found at {cookies_path}")
    exit(1)

try:
    conn = sqlite3.connect(cookies_path)
    cursor = conn.cursor()
    
    # Query for all cookies related to jianying or douyin
    query = "SELECT host_key, name, value, encrypted_value FROM cookies WHERE host_key LIKE '%jianying%' OR host_key LIKE '%douyin%'"
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} cookies:")
    for row in rows:
        host, name, value, encrypted_value = row
        val_display = value if value else "(encrypted)"
        if not value and len(encrypted_value) > 0:
            val_display = f"(encrypted {len(encrypted_value)} bytes)"
        print(f"Host: {host} | Name: {name} | Value: {val_display}")
            
    conn.close()

except sqlite3.Error as e:
    print(f"SQLite error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
