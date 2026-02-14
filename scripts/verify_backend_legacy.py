import sys
import os
import pandas as pd
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.backend as db

def test_legacy():
    print("Testing LEGACY functions...")
    
    # 1. obtener_compras_por_categoria
    try:
        d1 = date(2024, 1, 1)
        d2 = date(2025, 12, 31)
        df = db.obtener_compras_por_categoria(d1, d2)
        if isinstance(df, pd.DataFrame):
            print(f"✅ obtener_compras_por_categoria OK (Shape: {df.shape})")
        else:
            print(f"❌ obtener_compras_por_categoria returns {type(df)}")
    except Exception as e:
        print(f"❌ obtener_compras_por_categoria failed: {e}")

    # 2. obtener_historial_compras
    try:
        df = db.obtener_historial_compras()
        if isinstance(df, pd.DataFrame):
            print(f"✅ obtener_historial_compras OK (Shape: {df.shape})")
        else:
            print(f"❌ obtener_historial_compras returns {type(df)}")
    except Exception as e:
        print(f"❌ obtener_historial_compras failed: {e}")

    # 3. obtener_ordenes_compra
    try:
        df = db.obtener_ordenes_compra()
        if isinstance(df, pd.DataFrame):
            print(f"✅ obtener_ordenes_compra OK (Shape: {df.shape})")
        else:
            print(f"❌ obtener_ordenes_compra returns {type(df)}")
    except Exception as e:
        print(f"❌ obtener_ordenes_compra failed: {e}")

    # 4. calcular_valorizado_fifo
    try:
        val, mapa = db.calcular_valorizado_fifo(incluir_igv=True)
        print(f"✅ calcular_valorizado_fifo OK (Total: {val}, Items: {len(mapa)})")
    except Exception as e:
        print(f"❌ calcular_valorizado_fifo failed: {e}")

if __name__ == "__main__":
    test_legacy()
