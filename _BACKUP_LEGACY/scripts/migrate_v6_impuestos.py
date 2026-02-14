import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gestion_basica.db")

def migrate_v6():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        print("Iniciando migración V6 (Impuestos por Ítem)...")
        
        # Verificar si columna existe en compras_detalle
        cursor.execute("PRAGMA table_info(compras_detalle)")
        cols = [c[1] for c in cursor.fetchall()]
        
        if 'tasa_impuesto' not in cols:
            print("- Agregando columna 'tasa_impuesto' a 'compras_detalle'...")
            cursor.execute("ALTER TABLE compras_detalle ADD COLUMN tasa_impuesto REAL DEFAULT 18.0")
            
        conn.commit()
        print("Migración V6 completada.")
        
    except Exception as e:
        print(f"Error en migración: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_v6()
