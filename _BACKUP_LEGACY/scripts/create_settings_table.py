"""
Migración: Crear tabla de configuración
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def create_settings_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clave TEXT UNIQUE NOT NULL,
                valor TEXT,
                descripcion TEXT,
                fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insertar configuraciones por defecto
        default_settings = [
            ('nombre_empresa', 'Mi Empresa', 'Nombre de la empresa'),
            ('logo_path', '', 'Ruta del logo de la empresa'),
            ('moneda_principal', 'PEN', 'Moneda principal (PEN/USD)'),
            ('igv_default', '18', 'Tasa de IGV por defecto (%)'),
            ('almacen_principal', 'Almacén Principal', 'Nombre del almacén principal'),
        ]
        
        for clave, valor, desc in default_settings:
            cursor.execute("""
                INSERT OR IGNORE INTO configuracion (clave, valor, descripcion)
                VALUES (?, ?, ?)
            """, (clave, valor, desc))
        
        conn.commit()
        print("✅ Tabla 'configuracion' creada exitosamente")
        
        # Verificar
        cursor.execute("SELECT * FROM configuracion")
        configs = cursor.fetchall()
        print(f"\n📋 Configuraciones iniciales ({len(configs)}):")
        for cfg in configs:
            print(f"   - {cfg[1]}: {cfg[2]}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    create_settings_table()
