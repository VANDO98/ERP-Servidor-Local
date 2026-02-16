
import sys
import os

# Set backend as root for imports
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.database.db import get_connection
from src.auth.service import obtener_usuario_por_username
from src.auth.security import verify_password, get_username_hash

def debug_login(username, password):
    print(f"\n--- Debugging Login for '{username}' ---")
    
    # 1. Check raw DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user_row = cursor.fetchone()
    conn.close()
    
    if not user_row:
        print(f"[FAIL] User '{username}' not found in DB (Legacy search).")
        
        # Try hash search
        u_hash = get_username_hash(username)
        print(f"Trying hash search: {u_hash}")
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username_hash = ?", (u_hash,))
        user_row_hash = cursor.fetchone()
        conn.close()
        
        if not user_row_hash:
             print(f"[FAIL] User '{username}' not found in DB (Hash search).")
             return
        else:
             print(f"[OK] User found via Hash.")
             user_row = user_row_hash
    else:
        print(f"[OK] User found via Legacy username.")

    # 2. Check Password
    # column 2 is password_hash in schema: id, username, password_hash, ...
    stored_hash = user_row[2] 
    print(f"Stored Hash: {stored_hash}")
    
    is_valid = verify_password(password, stored_hash)
    
    if is_valid:
        print(f"[SUCCESS] Password is CORRECT.")
    else:
        print(f"[FAIL] Password is INCORRECT.")
        
        # Diagnostics
        try:
             import bcrypt
             print(f"Generated hash for '{password}': {bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()}")
        except:
             pass

if __name__ == "__main__":
    debug_login("admin", "admin")
