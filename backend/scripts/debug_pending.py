import sqlite3
import pandas as pd
import os

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/gestion_basica.db'))

def get_connection():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        # Try to find it in current directory
        cwd_db = os.path.join(os.getcwd(), 'tienda.db')
        if os.path.exists(cwd_db):
            print(f"Found in CWD: {cwd_db}")
            return sqlite3.connect(cwd_db)
        exit(1)
    return sqlite3.connect(DB_PATH)

def debug_orders():
    print(f"Using DB: {DB_PATH}")
    if os.path.exists(DB_PATH):
        print(f"DB Size: {os.path.getsize(DB_PATH)} bytes")

    conn = get_connection()
    cursor = conn.cursor()
    
    # List tables
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Tables found:", [t[0] for t in tables])
        
        if not tables:
            print("DATABASE IS EMPTY! Check path.")
            return
            
    except Exception as e:
        print(f"Error listing tables: {e}")
        return
    
    print("--- DEBUGGING PENDING ORDERS ---")
    
    try:
        # 1. Get ALL Approved/Pending Orders
        cursor.execute("SELECT id, estado, fecha_emision FROM ordenes_compra WHERE estado IN ('APROBADA', 'PENDIENTE', 'FACTURADA')")
        all_orders = cursor.fetchall()
        print(f"Total relevant orders found: {len(all_orders)}")
        
        for oid, estado, fecha in all_orders:
            print(f"\nEvaluating Order ID: {oid} ({estado})")
            
            # Get Ordered Qty
            cursor.execute("SELECT SUM(cantidad_solicitada) FROM ordenes_compra_det WHERE oc_id=?", (oid,))
            res_ordered = cursor.fetchone()
            qty_ordered = res_ordered[0] if res_ordered and res_ordered[0] is not None else 0.0
            
            # Get Received Qty
            cursor.execute("""
                SELECT SUM(d.cantidad_recibida) 
                FROM guias_remision_det d 
                JOIN guias_remision g ON d.guia_id = g.id 
                WHERE g.oc_id = ?
            """, (oid,))
            res_received = cursor.fetchone()
            qty_received = res_received[0] if res_received and res_received[0] is not None else 0.0
            
            print(f"  - Ordered: {qty_ordered}")
            print(f"  - Received: {qty_received}")
            print(f"  - Pending: {qty_ordered - qty_received}")
            print(f"  - Is Pending? {qty_received < qty_ordered}")

    # 2. Test the Actual Function Query (WITH PROOV JOIN)
    print("\n--- TESTING ACTUAL QUERY (WITH PROVIDER JOIN) ---")
    query = """
        SELECT 
            oc.id,
            oc.fecha_emision as fecha,
            p.razon_social as proveedor_nombre,
            (SELECT SUM(cantidad_solicitada) FROM ordenes_compra_det WHERE oc_id = oc.id) as total_ordered,
            COALESCE((
                SELECT SUM(d.cantidad_recibida) 
                FROM guias_remision_det d 
                JOIN guias_remision g ON d.guia_id = g.id 
                WHERE g.oc_id = oc.id
            ), 0) as total_received
        FROM ordenes_compra oc
        JOIN proveedores p ON oc.proveedor_id = p.id
        WHERE oc.estado IN ('APROBADA', 'PENDIENTE', 'FACTURADA')
        GROUP BY oc.id
        HAVING total_received < total_ordered
        ORDER BY oc.fecha_emision DESC
    """
    try:
        df = pd.read_sql(query, conn)
        print("Query Results:")
        print(df)
        if df.empty:
            print("WARNING: Query returned empty! Check PROVIDER IDs in orders vs proveedores table.")
            
            # Diagnostic: check separate counts
            cursor.execute("SELECT COUNT(*) FROM ordenes_compra WHERE estado IN ('APROBADA', 'PENDIENTE', 'FACTURADA')")
            cnt_oc = cursor.fetchone()[0]
            print(f"Pending OCs (Raw): {cnt_oc}")
            
            cursor.execute("SELECT COUNT(*) FROM ordenes_compra oc JOIN proveedores p ON oc.proveedor_id = p.id WHERE oc.estado IN ('APROBADA', 'PENDIENTE', 'FACTURADA')")
            cnt_join = cursor.fetchone()[0]
            print(f"Pending OCs (Joined): {cnt_join}")
            
    except Exception as e:
        print(f"Query Failed: {e}")

    except Exception as e:
        print(f"Error executing queries: {e}")
        import traceback
        traceback.print_exc()

    conn.close()

if __name__ == "__main__":
    debug_orders()
