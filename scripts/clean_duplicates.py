import sqlite3
import os

def get_db_path():
    if os.path.exists("data/gestion_basica.db"): return "data/gestion_basica.db"
    if os.path.exists("05_Gestion_Basica/data/gestion_basica.db"): return "05_Gestion_Basica/data/gestion_basica.db"
    return None

def clean_duplicates():
    db_path = get_db_path()
    if not db_path:
        print("DB not found")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Cleaning Duplicate Warehouses ---")
    
    # 1. Identify duplicates keeping the one with lowest ID
    cursor.execute("""
        DELETE FROM almacenes 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM almacenes 
            GROUP BY nombre
        )
    """)
    deleted = cursor.rowcount
    print(f"Removed {deleted} duplicate rows from 'almacenes'.")
    
    # 2. Show current
    rows = cursor.execute("SELECT * FROM almacenes").fetchall()
    print("Final Almacenes:")
    for r in rows:
        print(r)
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    clean_duplicates()
