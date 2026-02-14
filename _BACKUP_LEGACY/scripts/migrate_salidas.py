"""
Migración: Crear tablas de Salidas con esquema correcto
Ejecutar: python scripts/migrate_salidas.py
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Eliminar tablas antiguas si existen (con nombres incorrectos)
        cursor.execute("DROP TABLE IF EXISTS salidas")
        cursor.execute("DROP TABLE IF EXISTS salidas_detalle")
        
        # Crear tabla salidas_cabecera (nombre correcto)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS salidas_cabecera (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                tipo_salida TEXT DEFAULT 'Venta',
                destino TEXT,
                observaciones TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear tabla salidas_detalle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS salidas_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                salida_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad REAL NOT NULL,
                almacen_id INTEGER DEFAULT 1,
                costo_unitario REAL DEFAULT 0,
                FOREIGN KEY (salida_id) REFERENCES salidas_cabecera(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        """)
        
        conn.commit()
        print("✅ Tablas 'salidas_cabecera' y 'salidas_detalle' creadas/verificadas exitosamente")
        
        # Verificar si existen
        cursor.execute("SELECT COUNT(*) FROM salidas_cabecera")
        count_salidas = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM salidas_detalle")
        count_detalle = cursor.fetchone()[0]
        
        print(f"📊 Registros actuales:")
        print(f"   - salidas_cabecera: {count_salidas}")
        print(f"   - salidas_detalle: {count_detalle}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error en migración: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

