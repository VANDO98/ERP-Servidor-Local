import sqlite3
import os
import sys
import json

# Add backend to path
sys.path.insert(0, os.path.abspath("backend"))
from src.backend import (
    crear_producto, crear_proveedor, 
    crear_orden_compra_con_correlativo, 
    obtener_orden_compra,
    get_connection
)

def debug_oc_loading():
    print("🚀 Debugging OC Loading Logic...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Setup Data
        print("\n1. Setting up Test Data...")
        cursor.execute("DELETE FROM ordenes_compra WHERE observaciones = 'DEBUG_OC'")
        cursor.execute("DELETE FROM productos WHERE codigo_sku = 'DEBUG-SKU-999'")
        cursor.execute("DELETE FROM proveedores WHERE ruc_dni = '88888888888'")
        conn.commit()
        
        # Create Provider
        crear_proveedor("Debug Provider", "88888888888", "Debug Address", "123", "debug@test.com")
        cursor.execute("SELECT id FROM proveedores WHERE ruc_dni = '88888888888'")
        prov_id = cursor.fetchone()[0]
        
        # Create Product
        crear_producto("DEBUG-SKU-999", "Product Debug", "UND", 1, 10, 0)
        cursor.execute("SELECT id FROM productos WHERE codigo_sku = 'DEBUG-SKU-999'")
        prod_id = cursor.fetchone()[0]
        
        # 2. Create Purchase Order (OC)
        print("\n2. Creating Purchase Order...")
        items_oc = [{'pid': prod_id, 'cantidad': 50, 'precio_unitario': 20.0}]
        oc_id = crear_orden_compra_con_correlativo(
            prov_id, "2023-11-01", "2023-11-05", "PEN", 18, "DEBUG_OC", items_oc
        )
        print(f"   OC Created: ID {oc_id}")
        
        # 3. Retrieve OC using backend function
        print("\n3. Calling obtener_orden_compra(oc_id)...")
        oc_data = obtener_orden_compra(oc_id)
        
        print("\n   [RESULT DATA]:")
        print(json.dumps(oc_data, indent=4, default=str))
        
        # 4. Analyze for Frontend Layout
        # Frontend likely needs: 'pid', 'cantidad', 'precio_unitario' (or variations)
        # Check keys in items
        if oc_data and 'items' in oc_data:
            items = oc_data['items']
            print(f"\n   Found {len(items)} items.")
            if len(items) > 0:
                print("   Item 0 Keys:", list(items[0].keys()))
                
                # Check for critical keys
                required = ['pid', 'cantidad', 'precio_unitario', 'Producto', 'um']
                missing = [k for k in required if k not in items[0]]
                if missing:
                    print(f"   ❌ MISSING KEYS in Item: {missing}")
                else:
                    print("   ✅ All expected keys present for generic usage.")
        else:
            print("   ❌ No items found or data is None")

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    debug_oc_loading()
