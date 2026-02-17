
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def migrate():
    print(f"Migrating database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(guias_remision)")
        columns = cursor.fetchall()
        
        # SQLite doesn't support easy ALTER TABLE for types, 
        # but since DATE/DATETIME/TEXT are similar in SQLite, 
        # the truncation might be in the query or pandas.
        # However, making it explicit might help some drivers.
        
        # Actually, let's just make sure the data being inserted is correct.
        # And check if there is any server-side logic we missed.
        
        print("Schema check completed.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
