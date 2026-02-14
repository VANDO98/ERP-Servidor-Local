import pandas as pd
import src.backend as db

try:
    print("--- Testing obtener_productos_extendido ---")
    df = db.obtener_productos_extendido()
    if df.empty:
        print("DF is empty!")
    else:
        print(f"Rows: {len(df)}")
        print("Columns:", df.columns.tolist())
        
        # Simulate View Logic
        df['label'] = df.apply(lambda x: f"{x['codigo_sku'] or ''} | {x['nombre']}", axis=1)
        df['precio_ref_compra'] = df['ultimo_precio_compra'].fillna(0.0)
        
        print("\n--- Sample Rows ---")
        for i, row in df.head().iterrows():
            print(f"Product: {row['label']}")
            print(f"  ID: {row['id']}")
            print(f"  UM: {row['unidad_medida']}")
            print(f"  LastPrice: {row['ultimo_precio_compra']} -> Ref: {row['precio_ref_compra']}")
            
except Exception as e:
    print(f"Error: {e}")
