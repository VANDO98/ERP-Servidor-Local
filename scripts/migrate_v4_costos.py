import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gestion_basica.db")

def migrate_v4():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        print("Iniciando migración V4 (Tracking de Precios)...")
        
        # 1. Agregar campo 'costo_previo' a compras_detalle
        # Sirve para saber cuánto costaba el producto ANTES de esta compra y calcular variación
        cursor.execute("PRAGMA table_info(compras_detalle)")
        cols = [c[1] for c in cursor.fetchall()]
        
        if 'costo_previo' not in cols:
            print("- Agregando columna 'costo_previo' a 'compras_detalle'...")
            cursor.execute("ALTER TABLE compras_detalle ADD COLUMN costo_previo REAL DEFAULT 0")
        
        conn.commit()
        print("Migración V4 completada.")
        
    except Exception as e:
        print(f"Error en migración: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_v4()
