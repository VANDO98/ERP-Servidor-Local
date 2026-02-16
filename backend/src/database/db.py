
import sqlite3
import os
from src.auth.security import get_password_hash # Changed from src.auth to src.auth.security (anticipating move)

# Robust path handling
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Expected structure: backend/src/database/db.py -> backend/src/database -> backend/src -> backend
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def get_connection():
    """Retorna conexión a la base de datos"""
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initializes users table and default admin if empty"""
    print(f"Initializing database at: {DB_PATH}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                username_hash TEXT,
                username_encrypted TEXT
            )
        """)
        
        # Migration: Add columns if they don't exist
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN username_hash TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN username_encrypted TEXT")
            print("Migrated users table: Added username_hash and username_encrypted columns.")
        except sqlite3.OperationalError:
            pass # Columns likely exist
        
        # Check if empty
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            print("Creating default admin user...")
            pwd = "admin"[:72]
            admin_pwd = get_password_hash(pwd)
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                          ("admin", admin_pwd, "admin"))
            conn.commit()
            
    except Exception as e:
        print(f"Error initializing users db: {e}")
    finally:
        conn.close()
