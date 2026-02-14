import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gestion_basica.db")

def migrate_v5():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        print("Iniciando migración V5 (Soporte Multimoneda)...")
        
        # Verificar si columna existe
        cursor.execute("PRAGMA table_info(compras_cabecera)")
        cols = [c[1] for c in cursor.fetchall()]
        
        if 'tipo_cambio' not in cols:
            print("- Agregando columna 'tipo_cambio' a 'compras_cabecera'...")
            cursor.execute("ALTER TABLE compras_cabecera ADD COLUMN tipo_cambio REAL DEFAULT 1.0")
        
        conn.commit()
        print("Migración V5 completada.")
        
    except Exception as e:
        print(f"Error en migración: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_v5()
