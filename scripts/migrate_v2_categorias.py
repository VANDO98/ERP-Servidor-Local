import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gestion_basica.db")

def migrate():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        print("Iniciando migración V2...")
        
        # 1. Crear tabla CATEGORIAS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )
        """)
        print("- Tabla 'categorias' asegurada.")
        
        # 2. Insertar categoría por defecto 'General'
        cursor.execute("INSERT OR IGNORE INTO categorias (id, nombre) VALUES (1, 'General')")
        
        # 3. Verificar si 'productos' tiene 'categoria_id'
        cursor.execute("PRAGMA table_info(productos)")
        cols = cursor.fetchall()
        col_names = [c[1] for c in cols]
        
        if 'categoria_id' not in col_names:
            print("- Agregando columna 'categoria_id' a 'productos'...")
            # SQLite limitado: Agregamos columna con default 1
            cursor.execute("ALTER TABLE productos ADD COLUMN categoria_id INTEGER DEFAULT 1 REFERENCES categorias(id)")
        else:
            print("- Columna 'categoria_id' ya existe.")
            
        conn.commit()
        print("Migración completada exitosamente.")
        
    except Exception as e:
        print(f"Error en migración: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
