import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def update_test_stock_min():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # Primero ponemos un stock mínimo base a todos
        cursor.execute("UPDATE productos SET stock_minimo = 10")
        
        # Obtenemos algunos IDs para variar
        cursor.execute("SELECT id FROM productos LIMIT 5")
        ids = [row[0] for row in cursor.fetchall()]
        
        if ids:
            # Caso 1: Sin Stock (ya deben haber algunos con 0, les ponemos stock_min > 0)
            # Caso 2: Crítico (Stock <= 50% de Min)
            if len(ids) > 0:
                cursor.execute("UPDATE productos SET stock_minimo = 50 WHERE id = ?", (ids[0],))
            
            # Caso 3: Bajo (Stock <= Min)
            if len(ids) > 1:
                cursor.execute("UPDATE productos SET stock_minimo = 15 WHERE id = ?", (ids[1],))
                
        conn.commit()
        print("✅ Valores de prueba para stock_minimo actualizados.")
        
        # Mostrar resultado final
        cursor.execute("SELECT id, nombre, stock_actual, stock_minimo FROM productos")
        rows = cursor.fetchall()
        print(f"\n{'ID':<5} {'Nombre':<30} {'Stock Act':<10} {'Stock Min':<10}")
        print("-" * 60)
        for row in rows:
            print(f"{row[0]:<5} {row[1]:<30} {row[2]:<10} {row[3]:<10}")
            
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    update_test_stock_min()
