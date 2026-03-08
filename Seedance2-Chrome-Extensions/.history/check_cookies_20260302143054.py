import sqlite3
import os

# Path to the Cookies file
cookies_path = "playwright/user-data/Default/Cookies"

if not os.path.exists(cookies_path):
    print(f"Error: Cookies file not found at {cookies_path}")
    exit(1)

try:
    conn = sqlite3.connect(cookies_path)
    cursor = conn.cursor()
    
    # Query for cookies related to jimeng
    query = "SELECT host_key, name, value, path, expires_utc, is_secure, is_httponly, last_access_utc, has_expires, is_persistent, priority, encrypted_value, samesite, source_scheme, source_port, is_same_party FROM cookies WHERE host_key LIKE '%jimeng%'"
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} cookies for jimeng:")
    for row in rows:
        host, name, value, path, expires, secure, httponly, last_access, has_expires, persistent, priority, encrypted, samesite, scheme, port, same_party = row
        # value might be empty if encrypted_value is used
        val_display = value if value else "(encrypted)"
        print(f"Host: {host}, Name: {name}, Value: {val_display}")

    conn.close()

except sqlite3.Error as e:
    print(f"SQLite error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
