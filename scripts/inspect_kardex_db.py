import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def inspect_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    tables = ['compras_cabecera', 'compras_detalle', 'salidas_cabecera', 'salidas_detalle', 'productos']
    for table in tables:
        print(f"\n--- {table} ---")
        cursor.execute(f"PRAGMA table_info({table})")
        for col in cursor.fetchall():
            print(f"{col[1]} ({col[2]})")
    conn.close()

if __name__ == "__main__":
    inspect_schema()
