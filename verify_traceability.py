
import sys
import os
import pandas as pd

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# MOCK dependencies to avoid import errors
from unittest.mock import MagicMock
sys.modules['fastapi'] = MagicMock()
sys.modules['src.auth'] = MagicMock()

from src import backend as db

def run_verification():
    print("Starting Backend Traceability Verification...")
    
    # 1. Create OC
    print("1. Creating Order...")
    items = [
        {"pid": 1, "cantidad": 10, "precio_unitario": 100}
    ]
    
    try:
        oc_id = db.crear_orden_compra_con_correlativo(
            proveedor_id=1,
            fecha_emision="2023-10-27",
            fecha_entrega_estimada="2023-10-30",
            moneda="PEN",
            tasa_igv=18.0,
            observaciones="Test Traceability",
            items=items,
            direccion_entrega="Test Address 123"
        )
        print(f"Order Created: ID {oc_id}")
        
    except Exception as e:
        print(f"Error creating order: {e}")
        return

    # 2. Approve OC
    print(f"2. Approving Order {oc_id}...")
    db.actualizar_estado_oc(oc_id, "APROBADA")
    
    # 3. Register Purchase linked to OC
    print(f"3. Registering Purchase for OC {oc_id}...")
    purchase_data = {
        "proveedor_id": 1,
        "fecha": "2023-10-28",
        "serie": "F001",
        "numero": f"TEST-{oc_id}",
        "moneda": "PEN",
        "tasa_igv": 18.0,
        "tc": 3.85,
        "items": [
            {"pid": 1, "cantidad": 10, "precio_unitario": 100}
        ],
        "orden_compra_id": oc_id
    }
    
    ok, msg = db.registrar_compra(purchase_data)
    if not ok:
        print(f"Failed to register purchase: {msg}")
        return
    print("Purchase Registered")

    # 4. Verify OC Status
    print("4. Verifying OC Status and Address...")
    # obtener_orden_compra returns a dict/object or rows? In backend.py:
    # It returns a DICT constructed from fetches.
    # Wait, looking at backend.py ... obtaining logic:
    # "query_cab ... cursor.fetchone()"
    # It returns a dictionary.
    
    oc_data = db.obtener_orden_compra(oc_id)
    if not oc_data:
        print("Error: Could not retrieve OC data")
        return

    status = oc_data['estado']
    address = oc_data.get('direccion_entrega')

    if status == 'FACTURADA':
        print("PASS: OC Status is FACTURADA")
    else:
        print(f"FAIL: OC Status is {status}")

    if address == "Test Address 123":
        print("PASS: OC Address preserved")
    else:
        print(f"FAIL: OC Address mismatch: {address}")

    # 5. Verify Purchase Traceability
    print("5. Verifying Purchase Traceability...")
    df_hist = db.obtener_compras_historial()
    
    # Check if oc_id column exists
    if 'oc_id' not in df_hist.columns:
         print("FAIL: 'oc_id' column missing in history dataframe")
    else:
         # Find our purchase
         row = df_hist[df_hist['oc_id'] == oc_id]
         if not row.empty:
             print(f"PASS: Found Purchase linked to OC {oc_id}")
         else:
             print(f"FAIL: Purchase verification failed. oc_id {oc_id} not found in history.")

if __name__ == "__main__":
    run_verification()
