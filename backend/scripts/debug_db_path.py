
import os
import sqlite3
import sys

# Mimic the logic in db.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath("backend/src/database/db.py"))))
# Since we are running from root usually, let's just import the actual module to be sure what IT sees
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from src.database.db import DB_PATH, get_connection
except ImportError as e:
    print(f"Import Error: {e}")
    # Fallback to manual check of likely paths
    DB_PATH = "backend/data/gestion_basica.db"

print(f"--- Debugging DB Path ---")
print(f"Resolved DB_PATH: {DB_PATH}")

if os.path.exists(DB_PATH):
    print(f"[OK] File exists.")
    print(f"Size: {os.path.getsize(DB_PATH)} bytes")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"Tables found ({len(tables)}): {tables}")
    
    # Check record counts for key tables
    for t in ['users', 'productos', 'proveedores', 'compras_cabecera', 'stock_almacen']:
        if t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            count = cursor.fetchone()[0]
            print(f" - {t}: {count} records")
        else:
             print(f" - {t}: [MISSING TABLE]")
             
    conn.close()
else:
    print(f"[FAIL] File DOES NOT exist at {DB_PATH}")
    # Search for it
    print("Searching for .db files in current dir...")
    for root, dirs, files in os.walk("."):
        for f in files:
            if f.endswith(".db"):
                print(f"Found: {os.path.join(root, f)}")
