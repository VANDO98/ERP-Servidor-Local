import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gestion_basica.db")

def migrate():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        print("Iniciando migración V3 (Unidad Medida en Detalle)...")
        
        # Verificar si columna existe
        cursor.execute("PRAGMA table_info(compras_detalle)")
        cols = cursor.fetchall()
        col_names = [c[1] for c in cols]
        
        if 'unidad_medida' not in col_names:
            print("- Agregando columna 'unidad_medida' a 'compras_detalle'...")
            cursor.execute("ALTER TABLE compras_detalle ADD COLUMN unidad_medida TEXT DEFAULT 'UND'")
        else:
            print("- Columna 'unidad_medida' ya existe.")
            
        conn.commit()
        print("Migración V3 completada.")
        
    except Exception as e:
        print(f"Error en migración: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
