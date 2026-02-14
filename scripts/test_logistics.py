import src.backend as db
from datetime import date
import pandas as pd

def test_traslados():
    print("--- Testing Traslados ---")
    
    # 1. Setup Data
    print("Getting Almacenes...")
    df_alm = db.obtener_almacenes()
    if len(df_alm) < 2:
        print("❌ Need at least 2 warehouses")
        return
        
    id_origen = df_alm.iloc[0]['id'] # Principal
    id_destino = df_alm.iloc[1]['id'] # Norte
    
    print(f"Origen: {id_origen}, Destino: {id_destino}")
    
    # 2. Get Product with Stock
    df_prods = db.obtener_productos_extendido()
    stock_pds = df_prods[df_prods['stock_actual'] > 10]
    
    if stock_pds.empty:
        print("❌ No products with > 10 stock to transfer")
        return
        
    row = stock_pds.iloc[0]
    pid = int(row['id'])
    print(f"Product: {row['nombre']} (ID: {pid}), Stock Global: {row['stock_actual']}")

    # 3. Exec Transfer
    # Ensure source has stock (Stock Global might be distributed, so check stock_almacen directly)
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT stock_actual FROM stock_almacen WHERE producto_id=? AND almacen_id=?", (pid, id_origen))
    res = c.fetchone()
    conn.close()
    
    if not res or res[0] < 5:
        print(f"⚠️ Stock in Origin {id_origen} too low ({res[0] if res else 0}). Skipping actual transfer.")
        return

    qty = 2.0
    cab = {
        "fecha": date.today(),
        "origen_id": int(id_origen),
        "destino_id": int(id_destino),
        "observaciones": "Test Script Transfer"
    }
    
    detalles = [{
        "pid": pid,
        "cantidad": qty
    }]
    
    print(f"Transferring {qty} units...")
    ok, msg = db.registrar_traslado(cab, detalles)
    
    if ok:
        print(f"✅ Success: {msg}")
    else:
        print(f"❌ Failed: {msg}")
        
    # 4. Verify History
    print("Verifying History...")
    df_h = db.obtener_historial_traslados()
    print(df_h.head())
    
    # 5. Verify Search
    print("Verifying Search...")
    df_s = db.obtener_stock_por_almacen(pid)
    print(df_s)

if __name__ == "__main__":
    test_traslados()
