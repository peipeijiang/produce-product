import sqlite3
import os

cookies_path = "playwright/user-data/Default/Cookies"

if not os.path.exists(cookies_path):
    print(f"Error: Cookies file not found at {cookies_path}")
    exit(1)

try:
    conn = sqlite3.connect(cookies_path)
    cursor = conn.cursor()
    
    # Query for all cookies related to jimeng
    query = "SELECT host_key, name, value, path, expires_utc, is_secure, is_httponly FROM cookies WHERE host_key LIKE '%jimeng%'"
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        print(f"I found {len(rows)} cookies containing 'jimeng' in host_key:")
        for row in rows:
            host, name, value, path, expires, secure, httponly = row
            # value might be empty if encrypted_value is used
            val_display = value if value else "(encrypted)"
            print(f"- {name}: {val_display}")
            
    except sqlite3.OperationalError as e:
        print(f"Query error: {e}")
        # Try to select all to see column names
        cursor.execute("PRAGMA table_info(cookies)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Columns in 'cookies' table: {columns}")
        
    conn.close()

except sqlite3.Error as e:
    print(f"SQLite error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
