import sqlite3
import os

DB_PATH = os.path.join("data", "gestion_basica.db")

def check():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check table
    res = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='almacenes'").fetchone()
    if res:
        print("✅ Table 'almacenes' exists.")
        # Check content
        rows = cursor.execute("SELECT * FROM almacenes").fetchall()
        print(f"   Rows: {rows}")
    else:
        print("❌ Table 'almacenes' DOES NOT exist.")
        
    conn.close()

if __name__ == "__main__":
    check()
