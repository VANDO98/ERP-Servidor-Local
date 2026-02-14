import sqlite3
import pandas as pd
from datetime import datetime
import os

# Mocking a temporary DB environment for testing the logic
DB_TEST = "test_fifo_logic.db"

def setup_test_db():
    if os.path.exists(DB_TEST):
        os.remove(DB_TEST)
    conn = sqlite3.connect(DB_TEST)
    cursor = conn.cursor()
    
    # Simple schema for testing
    cursor.execute("CREATE TABLE productos (id INTEGER PRIMARY KEY, nombre TEXT, stock_actual REAL)")
    cursor.execute("""
        CREATE TABLE compras_cabecera (
            id INTEGER PRIMARY KEY, 
            fecha_emision DATE, 
            moneda TEXT, 
            tipo_cambio REAL,
            fecha_registro TIMESTAMP
        )
    """)
    cursor.execute("CREATE TABLE compras_detalle (id INTEGER PRIMARY KEY, compra_id INTEGER, producto_id INTEGER, cantidad REAL, precio_unitario REAL)")
    cursor.execute("CREATE TABLE salidas_cabecera (id INTEGER PRIMARY KEY, fecha DATE, tipo_salida TEXT, fecha_registro TIMESTAMP)")
    cursor.execute("CREATE TABLE salidas_detalle (id INTEGER PRIMARY KEY, salida_id INTEGER, producto_id INTEGER, cantidad REAL)")
    
    # 1. Product
    cursor.execute("INSERT INTO productos (id, nombre, stock_actual) VALUES (1, 'Test Product', 0)")
    
    # 2. Entries (FIFO batches)
    # Batch 1: 10 units at S/ 100
    cursor.execute("INSERT INTO compras_cabecera (id, fecha_emision, moneda, tipo_cambio, fecha_registro) VALUES (1, '2026-01-01', 'PEN', 1.0, '2026-01-01 10:00:00')")
    cursor.execute("INSERT INTO compras_detalle (compra_id, producto_id, cantidad, precio_unitario) VALUES (1, 1, 10, 100)")
    
    # Batch 2: 10 units at S/ 150
    cursor.execute("INSERT INTO compras_cabecera (id, fecha_emision, moneda, tipo_cambio, fecha_registro) VALUES (2, '2026-01-05', 'PEN', 1.0, '2026-01-05 10:00:00')")
    cursor.execute("INSERT INTO compras_detalle (compra_id, producto_id, cantidad, precio_unitario) VALUES (2, 1, 10, 150)")
    
    # 3. Exits
    # Exit 1: 5 units on 2026-02-01 (should cost 5 * 100 = 500)
    cursor.execute("INSERT INTO salidas_cabecera (id, fecha, tipo_salida, fecha_registro) VALUES (1, '2026-02-01', 'VENTA', '2026-02-01 12:00:00')")
    cursor.execute("INSERT INTO salidas_detalle (salida_id, producto_id, cantidad) VALUES (1, 1, 5)")
    
    # Exit 2: 7 units on 2026-02-05 (should cost 5 * 100 + 2 * 150 = 500 + 300 = 800)
    cursor.execute("INSERT INTO salidas_cabecera (id, fecha, tipo_salida, fecha_registro) VALUES (2, '2026-02-05', 'VENTA', '2026-02-05 12:00:00')")
    cursor.execute("INSERT INTO salidas_detalle (salida_id, producto_id, cantidad) VALUES (2, 1, 7)")
    
    conn.commit()
    return conn

def run_fifo_valuation_logic(conn, start_date, end_date):
    # This is a port of the logic in backend.py adapted for the test db
    valor_total_salidas_periodo = 0.0
    
    query_prod = "SELECT DISTINCT producto_id FROM salidas_detalle sd JOIN salidas_cabecera sc ON sd.salida_id = sc.id WHERE sc.fecha BETWEEN ? AND ?"
    df_pids = pd.read_sql(query_prod, conn, params=(start_date, end_date))
    
    for pid in df_pids['producto_id']:
        q_ent = """
            SELECT cd.cantidad, cd.precio_unitario, cc.fecha_emision, cc.moneda, cc.tipo_cambio
            FROM compras_detalle cd
            JOIN compras_cabecera cc ON cd.compra_id = cc.id
            WHERE cd.producto_id = ?
            ORDER BY cc.fecha_emision ASC, cc.id ASC
        """
        df_ent = pd.read_sql(q_ent, conn, params=(int(pid),))
        
        q_sal = """
            SELECT sd.cantidad, sc.fecha, sc.id as salida_id
            FROM salidas_detalle sd
            JOIN salidas_cabecera sc ON sd.salida_id = sc.id
            WHERE sd.producto_id = ?
            ORDER BY sc.fecha ASC, sc.id ASC
        """
        df_sal = pd.read_sql(q_sal, conn, params=(int(pid),))
        
        batches = []
        for _, row in df_ent.iterrows():
            batches.append({'qty': row['cantidad'], 'price': row['precio_unitario']})
            
        for _, row_s in df_sal.iterrows():
            qty_to_consume = row_s['cantidad']
            salida_fecha = row_s['fecha']
            valor_esta_salida = 0.0
            
            while qty_to_consume > 0 and batches:
                batch = batches[0]
                if batch['qty'] <= qty_to_consume:
                    valor_esta_salida += batch['qty'] * batch['price']
                    qty_to_consume -= batch['qty']
                    batches.pop(0)
                else:
                    valor_esta_salida += qty_to_consume * batch['price']
                    batch['qty'] -= qty_to_consume
                    qty_to_consume = 0
            
            if start_date <= str(salida_fecha) <= end_date:
                valor_total_salidas_periodo += valor_esta_salida
                
    return valor_total_salidas_periodo

if __name__ == "__main__":
    conn = setup_test_db()
    
    # Range covering both exits
    res1 = run_fifo_valuation_logic(conn, '2026-02-01', '2026-02-28')
    print(f"Test 1 (Full Range): Expected 1300.0, Got {res1}")
    assert res1 == 1300.0
    
    # Range covering only first exit
    res2 = run_fifo_valuation_logic(conn, '2026-02-01', '2026-02-01')
    print(f"Test 2 (Single day): Expected 500.0, Got {res2}")
    assert res2 == 500.0
    
    # Range covering only second exit
    res3 = run_fifo_valuation_logic(conn, '2026-02-05', '2026-02-05')
    print(f"Test 3 (Single day): Expected 800.0, Got {res3}")
    assert res3 == 800.0
    
    conn.close()
    os.remove(DB_TEST)
    print("FIFO Exit Valuation Verification PASSED! ✅")
