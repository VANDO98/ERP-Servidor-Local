
import sqlite3
import os

DB_PATH = 'backend/data/gestion_basica.db'

def list_tables():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for t in tables:
        table_name = t[0]
        print(f"\nTABLE: {table_name}")
        cursor.execute(f"PRAGMA table_info({table_name})")
        cols = cursor.fetchall()
        for c in cols:
            print(f"  - {c[1]} ({c[2]})")
            
    conn.close()

if __name__ == "__main__":
    list_tables()
