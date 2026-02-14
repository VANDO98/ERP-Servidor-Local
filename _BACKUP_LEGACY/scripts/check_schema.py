import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def check_table(table_name):
    print(f"\n--- {table_name} ---")
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        cols = cursor.fetchall()
        for c in cols:
            print(f" - {c[1]} ({c[2]})")
    except Exception as e:
        print(f"Error: {e}")

check_table("ordenes_compra")
check_table("ordenes_compra_det")
check_table("salidas_cabecera")
check_table("salidas_detalle")

conn.close()
