import sqlite3
import os

DB_PATH = os.path.join("data", "gestion_basica.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    # Check if column exists
    cursor.execute("PRAGMA table_info(compras_cabecera)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if "orden_compra_id" not in columns:
        print("Adding orden_compra_id column...")
        cursor.execute("ALTER TABLE compras_cabecera ADD COLUMN orden_compra_id INTEGER REFERENCES ordenes_compra(id)")
        conn.commit()
        print("Column added successfully.")
    else:
        print("Column orden_compra_id already exists.")

except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
