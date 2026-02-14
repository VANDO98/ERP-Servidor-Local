"""
Script para verificar y corregir el esquema de salidas_cabecera
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def fix_salidas_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar esquema actual
        cursor.execute("PRAGMA table_info(salidas_cabecera)")
        columns = cursor.fetchall()
        
        print("📋 Esquema actual de salidas_cabecera:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Eliminar y recrear con esquema correcto
        print("\n🔄 Recreando tabla con esquema correcto...")
        
        cursor.execute("DROP TABLE IF EXISTS salidas_detalle")
        cursor.execute("DROP TABLE IF EXISTS salidas_cabecera")
        
        # Crear salidas_cabecera con TODAS las columnas necesarias
        cursor.execute("""
            CREATE TABLE salidas_cabecera (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                tipo_salida TEXT DEFAULT 'Venta',
                destino TEXT,
                observaciones TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear salidas_detalle
        cursor.execute("""
            CREATE TABLE salidas_detalle (
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
        
        # Verificar nuevo esquema
        cursor.execute("PRAGMA table_info(salidas_cabecera)")
        new_columns = cursor.fetchall()
        
        print("\n✅ Nuevo esquema de salidas_cabecera:")
        for col in new_columns:
            print(f"   - {col[1]} ({col[2]})")
        
        print("\n✅ Tablas recreadas exitosamente")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    fix_salidas_schema()
