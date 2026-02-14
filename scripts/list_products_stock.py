import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def list_products():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nombre, stock_actual, stock_minimo FROM productos")
        rows = cursor.fetchall()
        print(f"{'ID':<5} {'Nombre':<30} {'Stock Act':<10} {'Stock Min':<10}")
        print("-" * 60)
        for row in rows:
            print(f"{row[0]:<5} {row[1]:<30} {row[2]:<10} {row[3]:<10}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    list_products()
