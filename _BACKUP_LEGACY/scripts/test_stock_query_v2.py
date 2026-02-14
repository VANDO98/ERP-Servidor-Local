import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def test_query():
    conn = sqlite3.connect(DB_PATH)
    
    # Probamos alternativa usando subquery para evitar HAVING problemático
    query_alt = """
        SELECT * FROM (
            SELECT 
                p.nombre as Producto,
                p.stock_actual as Stock,
                p.unidad_medida as UM,
                p.stock_minimo as StockMinimo,
                CASE 
                    WHEN p.stock_actual <= 0 THEN 'Sin Stock'
                    WHEN p.stock_minimo > 0 AND p.stock_actual <= p.stock_minimo * 0.5 THEN 'Crítico'
                    WHEN p.stock_minimo > 0 AND p.stock_actual <= p.stock_minimo THEN 'Bajo'
                    ELSE 'Normal'
                END as Estado
            FROM productos p
            WHERE p.stock_minimo > 0
        ) 
        WHERE Estado IN ('Sin Stock', 'Crítico', 'Bajo')
    """
    try:
        print("\nEjecutando consulta alternativa (subquery)...")
        df_alt = pd.read_sql(query_alt, conn)
        print(f"Resultados: {len(df_alt)}")
        if len(df_alt) > 0:
            print(df_alt.head(10))
    except Exception as e:
        print(f"Error en query_alt: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_query()
