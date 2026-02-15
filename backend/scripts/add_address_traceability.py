
import sqlite3
import os

DB_PATH = 'backend/data/gestion_basica.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Migrating schema...")

    # 1. Add direccion_entrega to ordenes_compra
    try:
        cursor.execute("ALTER TABLE ordenes_compra ADD COLUMN direccion_entrega TEXT")
        print("Added direccion_entrega to ordenes_compra")
    except sqlite3.OperationalError:
        print("direccion_entrega already exists in ordenes_compra")

    # 2. Add oc_id to compras_cabecera
    # Note: Backend uses 'compras_cabecera', check_traceability showed no 'compras' table.
    try:
        cursor.execute("ALTER TABLE compras_cabecera ADD COLUMN oc_id INTEGER")
        print("Added oc_id to compras_cabecera")
    except sqlite3.OperationalError:
        print("oc_id already exists in compras_cabecera")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
