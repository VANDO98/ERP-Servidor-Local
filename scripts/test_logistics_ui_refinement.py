import src.backend as db
import pandas as pd

def test_ui_refinement():
    print("--- Verifying Logistics UI Refinement ---")
    
    # 1. Check Dynamic Stock Function
    print("\n1. Testing 'obtener_productos_con_stock_por_almacen' for Warehouse ID 1...")
    df_prods = db.obtener_productos_con_stock_por_almacen(1)
    
    if df_prods.empty:
        print("❌ No products returned.")
    else:
        # Check columns
        required_cols = ['stock_almacen', 'stock_global', 'unidad_medida']
        if all(col in df_prods.columns for col in required_cols):
            print("✅ Function returns correct columns (stock_almacen, stock_global, unidad_medida).")
            print("Sample Row:")
            print(df_prods.iloc[0][['nombre', 'stock_almacen', 'stock_global']])
        else:
            print(f"❌ Missing columns. Found: {df_prods.columns}")

    # 2. Check History U.M.
    print("\n2. Testing 'obtener_historial_traslados' for U.M. column...")
    df_hist= db.obtener_historial_traslados()
    
    if 'UMs' in df_hist.columns:
        print("✅ Column 'UMs' found in history.")
        print("Sample History:")
        print(df_hist.head(1)[['id', 'UMs']])
    else:
        print(f"❌ Column 'UMs' NOT found. Columns: {df_hist.columns}")

if __name__ == "__main__":
    test_ui_refinement()
