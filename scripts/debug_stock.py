import sqlite3
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

conn = sqlite3.connect(DB_PATH)

print("--- ANALISIS DE MONEDAS ---")
try:
    df_moneda = pd.read_sql("SELECT moneda, COUNT(*) as docs, SUM(total_compra) as total_nominal FROM compras_cabecera GROUP BY moneda", conn)
    print(df_moneda)
except Exception as e:
    print(f"Error monedas: {e}")

print("\n--- ANALISIS DE STOCK INICIAL (FANTASMA) ---")
# Compare Physical Stock vs Logic Flow
query = """
    SELECT 
        p.id, p.nombre, 
        COALESCE(sa.stock_actual, 0) as stock_fisico,
        COALESCE(c.entradas, 0) as entradas,
        COALESCE(s.salidas, 0) as salidas,
        (COALESCE(c.entradas, 0) - COALESCE(s.salidas, 0)) as stock_teorico_flujo,
        (COALESCE(sa.stock_actual, 0) - (COALESCE(c.entradas, 0) - COALESCE(s.salidas, 0))) as diferencia_inicial
    FROM productos p
    LEFT JOIN (SELECT producto_id, SUM(stock_actual) as stock_actual FROM stock_almacen GROUP BY producto_id) sa ON p.id = sa.producto_id
    LEFT JOIN (SELECT producto_id, SUM(cantidad) as entradas FROM compras_detalle GROUP BY producto_id) c ON p.id = c.producto_id
    LEFT JOIN (SELECT producto_id, SUM(cantidad) as salidas FROM salidas_detalle GROUP BY producto_id) s ON p.id = s.producto_id
    WHERE diferencia_inicial != 0 OR stock_fisico > 0
"""
df_stock = pd.read_sql(query, conn)
print(df_stock)

print("\n--- PRODUCTOS SIN COMPRAS PERO CON STOCK ---")
print(df_stock[df_stock['entradas'] == 0])

conn.close()
