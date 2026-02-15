import sqlite3
import os
import sys
import json

# Add backend to path
sys.path.insert(0, os.path.abspath("backend"))
from src.backend import (
    crear_producto, crear_proveedor, 
    crear_orden_compra_con_correlativo, 
    obtener_saldo_oc,
    get_connection
)

def test_balance_endpoint_logic():
    print("🚀 Testing Balance Logic for Endpoint...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Setup Data
        cursor.execute("DELETE FROM ordenes_compra WHERE observaciones = 'BALANCE_TEST'")
        cursor.execute("DELETE FROM productos WHERE codigo_sku = 'BAL-SKU-888'")
        conn.commit()
        
        # Create Provider & Product
        cursor.execute("SELECT id FROM proveedores LIMIT 1")
        prov_id = cursor.fetchone()[0]
        
        crear_producto("BAL-SKU-888", "Product Balance", "UND", 1, 10, 0)
        cursor.execute("SELECT id FROM productos WHERE codigo_sku = 'BAL-SKU-888'")
        prod_id = cursor.fetchone()[0]
        
        # Create Purchase Order (OC) - Qty 50
        print("\nCreating Purchase Order (Qty: 50)...")
        items_oc = [{'pid': prod_id, 'cantidad': 50, 'precio_unitario': 20.0}]
        oc_id = crear_orden_compra_con_correlativo(
            prov_id, "2023-11-01", "2023-11-05", "PEN", 18, "BALANCE_TEST", items_oc
        )
        print(f"OC Created: ID {oc_id}")
        
        # Call Logic corresponding to /api/orders/{oid}/balance
        print(f"\nCalling obtener_saldo_oc({oc_id})...")
        balance_data = obtener_saldo_oc(oc_id)
        
        print("\n[RESULT DATA]:")
        print(json.dumps(balance_data, indent=4, default=str))
        
        if balance_data and balance_data.get('fully_completed') is False:
             print("✅ Logic Correct: Order is not fully completed.")
             items = balance_data.get('items', [])
             if items and items[0].get('cantidad_pendiente') == 50:
                 print("✅ Logic Correct: Pending quantity is 50.")
             else:
                 print("❌ Logic Error: Pending quantity mismatch.")
        else:
             print("❌ Logic Error: Unexpected status.")

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    test_balance_endpoint_logic()
