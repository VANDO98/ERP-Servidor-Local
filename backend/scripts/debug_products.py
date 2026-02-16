
import sys
import os
import pandas as pd

# Setup path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.database.db import get_connection

def debug_products():
    print("--- Debugging Product Retrieval ---")
    conn = get_connection()
    try:
        # 1. Simple Select
        print("1. Testing simple SELECT from productos...")
        df_simple = pd.read_sql("SELECT * FROM productos LIMIT 5", conn)
        print(f"   Rows found: {len(df_simple)}")
        print(df_simple.head())
        
        # 2. Testing the complex query from service
        print("\n2. Testing Service Query (Joined)...")
        query = """
            SELECT p.id, p.nombre, p.codigo_sku, c.nombre as categoria_nombre, 
                   p.unidad_medida, p.stock_actual, p.stock_minimo, p.costo_promedio, p.precio_venta
            FROM productos p
            LEFT JOIN categorias c ON p.categoria_id = c.id
        """
        df_complex = pd.read_sql(query, conn)
        print(f"   Rows found: {len(df_complex)}")
        print(df_complex.head())
        
    except Exception as e:
        print(f"\n[ERROR]: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    debug_products()
