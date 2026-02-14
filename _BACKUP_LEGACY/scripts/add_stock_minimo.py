"""
Migración: Agregar columna stock_minimo a tabla productos
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def add_stock_minimo():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(productos)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'stock_minimo' in columns:
            print("✅ La columna 'stock_minimo' ya existe")
        else:
            print("➕ Agregando columna 'stock_minimo' a tabla productos...")
            cursor.execute("""
                ALTER TABLE productos 
                ADD COLUMN stock_minimo REAL DEFAULT 0
            """)
            conn.commit()
            print("✅ Columna 'stock_minimo' agregada exitosamente")
        
        # Verificar esquema actualizado
        cursor.execute("PRAGMA table_info(productos)")
        print("\n📋 Columnas de productos:")
        for col in cursor.fetchall():
            print(f"   - {col[1]} ({col[2]})")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    add_stock_minimo()
