
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def migrate():
    print(f"Migrating database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Add subcategoria to productos
        cursor.execute("ALTER TABLE productos ADD COLUMN subcategoria TEXT DEFAULT ''")
        print("Success: Added 'subcategoria' column to 'productos' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Notice: 'subcategoria' column already exists.")
        else:
            print(f"Error: {e}")
    finally:
        conn.commit()
        conn.close()

if __name__ == "__main__":
    migrate()
