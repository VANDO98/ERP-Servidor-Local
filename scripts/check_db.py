import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gestion_basica.db")

try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Obtener lista de tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()
    
    print(f"--- ESTRUCTURA DE LA BASE DE DATOS ({DB_NAME}) ---")
    print(f"Total de tablas encontradas: {len(tablas)}")
    
    for tabla in tablas:
        nombre_tabla = tabla[0]
        if nombre_tabla == "sqlite_sequence": continue # Omitir interna
        
        print(f"\n[TABLA] {nombre_tabla}")
        # Obtener columnas
        cursor.execute(f"PRAGMA table_info({nombre_tabla})")
        columnas = cursor.fetchall()
        for col in columnas:
            # col[1] es nombre, col[2] es tipo
            print(f"  - {col[1]} ({col[2]})")
            
    conn.close()
except Exception as e:
    print(f"Error: {e}")
