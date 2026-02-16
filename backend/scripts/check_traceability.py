
import sqlite3
import pandas as pd

DB_PATH = 'backend/data/gestion_basica.db'

def check_traceability_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n--- compras columns ---")
    try:
        cursor.execute("PRAGMA table_info(compras)")
        cols = cursor.fetchall()
        for c in cols:
            print(c[1])
    except:
        print("Table 'compras' not found")

    print("\n--- guias columns ---")
    try:
        cursor.execute("PRAGMA table_info(guias_remision)")
        cols = cursor.fetchall()
        if not cols:
            print("Table 'guias_remision' not found")
        else:
            for c in cols:
                print(c[1])
    except:
        print("Error checking guias")

    conn.close()

if __name__ == "__main__":
    check_traceability_schema()
