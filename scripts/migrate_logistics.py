import sqlite3
import os

def get_db_path():
    # Try current dir
    if os.path.exists("data/gestion_basica.db"):
        return "data/gestion_basica.db"
    # Try one level up (if running from scripts/)
    if os.path.exists("../data/gestion_basica.db"):
        return "../data/gestion_basica.db"
    # Try full path structure
    if os.path.exists("05_Gestion_Basica/data/gestion_basica.db"):
        return "05_Gestion_Basica/data/gestion_basica.db"
    return None

def migrate_logistics():
    db_path = get_db_path()
    if not db_path:
        print("❌ DB not found!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"--- Starting Logistics Migration on {db_path} ---")

    # 1. Add almacen_id to compras_detalle
    print("Checking 'compras_detalle' for 'almacen_id'...")
    try:
        cursor.execute("SELECT almacen_id FROM compras_detalle LIMIT 1")
        print("✅ 'almacen_id' already exists in 'compras_detalle'.")
    except sqlite3.OperationalError:
        print("⚠️ 'almacen_id' missing. Adding column...")
        try:
            # SQLite does not support adding column with default value easily if not null, 
            # but for simple cases:
            cursor.execute("ALTER TABLE compras_detalle ADD COLUMN almacen_id INTEGER DEFAULT 1")
            print("✅ Column 'almacen_id' added successfully.")
        except Exception as e:
            print(f"❌ Error adding column: {e}")

    # 2. Create traslados_cabecera
    print("Creating 'traslados_cabecera'...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traslados_cabecera (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE,
            origen_id INTEGER,
            destino_id INTEGER,
            observaciones TEXT,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            estado TEXT DEFAULT 'COMPLETADO',
            FOREIGN KEY(origen_id) REFERENCES almacenes(id),
            FOREIGN KEY(destino_id) REFERENCES almacenes(id)
        )
    """)
    
    # 3. Create traslados_detalle
    print("Creating 'traslados_detalle'...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traslados_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            traslado_id INTEGER,
            producto_id INTEGER,
            cantidad REAL,
            costo_unitario REAL,
            FOREIGN KEY(traslado_id) REFERENCES traslados_cabecera(id),
            FOREIGN KEY(producto_id) REFERENCES productos(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("--- Migration Completed ---")

if __name__ == "__main__":
    migrate_logistics()
