import sys
import os
import sqlite3

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend import init_users_db, get_connection, obtener_usuario_por_username
from src.auth import verify_password

def verify_setup():
    print("--- Verifying Auth Setup ---")
    
    # 1. Initialize DB (Create table if missing)
    print("1. Running init_users_db()...")
    init_users_db()
    
    # 2. Check Table
    print("2. Checking 'users' table...")
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            print("   ✅ Table 'users' exists.")
        else:
            print("   ❌ Table 'users' MISSING!")
            return
            
        # 3. Check Admin
        print("3. Checking default admin...")
        cursor.execute("SELECT * FROM users WHERE username='admin'")
        admin = cursor.fetchone()
        if admin:
            print(f"   ✅ User 'admin' found (ID: {admin[0]}, Role: {admin[3]}).")
            
            # 4. Verify Password
            print("4. Verifying default password ('admin')...")
            # hash is index 2
            pwd_hash = admin[2]
            if verify_password("admin", pwd_hash):
                print("   ✅ Password verification SUCCESS.")
            else:
                 print("   ❌ Password verification FAILED.")
        else:
            print("   ❌ User 'admin' NOT FOUND.")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        conn.close()
        
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    verify_setup()
