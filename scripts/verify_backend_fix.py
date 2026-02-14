import sys
import os
import pandas as pd
from datetime import date

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.backend as db

def test_backend():
    print("Testing backend functions...")
    
    # 1. obtener_proveedores
    try:
        df = db.obtener_proveedores()
        if isinstance(df, pd.DataFrame):
            print(f"✅ obtener_proveedores returns DataFrame (Shape: {df.shape})")
        else:
            print(f"❌ obtener_proveedores returns {type(df)}")
    except Exception as e:
        print(f"❌ obtener_proveedores failed: {e}")

    # 2. obtener_productos
    try:
        df = db.obtener_productos()
        if isinstance(df, pd.DataFrame):
            print(f"✅ obtener_productos returns DataFrame (Shape: {df.shape})")
        else:
            print(f"❌ obtener_productos returns {type(df)}")
    except Exception as e:
        print(f"❌ obtener_productos failed: {e}")

    # 3. obtener_top_proveedores
    try:
        d1 = date(2024, 1, 1)
        d2 = date(2025, 12, 31)
        df = db.obtener_top_proveedores(d1, d2)
        if isinstance(df, pd.DataFrame):
            print(f"✅ obtener_top_proveedores returns DataFrame (Shape: {df.shape})")
        else:
            print(f"❌ obtener_top_proveedores returns {type(df)}")
    except Exception as e:
        print(f"❌ obtener_top_proveedores failed: {e}")

if __name__ == "__main__":
    test_backend()
