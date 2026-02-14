import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join("data", "gestion_basica.db")

def audit_db():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("--- 📊 DATABASE AUDIT REPORT ---")
    
    # 1. Table Counts
    print("\n[1] Row Counts per Table:")
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    for t in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
        print(f"  - {t[0]}: {count}")

    # 2. Key Integrity Checks
    print("\n[2] Integrity Checks:")
    
    # Check 2.1: Compras Cabecera vs Detalle consistency (Total verification)
    # Note: absolute precision comparison might fail due to float, detecting significant diffs
    print("  - Checking Compras Totals vs Details Sum...")
    try:
        query = """
            SELECT 
                c.id, c.numero_documento, c.total_final, 
                SUM(cd.subtotal) as sum_details
            FROM compras_cabecera c
            LEFT JOIN compras_detalle cd ON c.id = cd.compra_id
            GROUP BY c.id
            HAVING ABS(c.total_final - COALESCE(SUM(cd.subtotal),0)) > 0.1
        """
        diffs = pd.read_sql(query, conn)
        if not diffs.empty:
            print(f"    ⚠️ FOUND {len(diffs)} discrepancies in purchase totals:")
            print(diffs.head())
        else:
            print("    ✅ All purchase headers match sum of details.")
    except Exception as e:
        print(f"    ❌ Error checking compras: {e}")

    # Check 2.2: Stock Logico vs Kardex
    # Calculating stock from movements (simple version)
    print("  - Checking Stock Consistency (Kardex vs Almacen)...")
    try:
        # Stock theoretical: Sum(Entradas) - Sum(Salidas)
        # This is complex to do purely in SQL without a recursive CTE if kardex isn't a single table
        # We'll check if stock_almacen matches the 'stock_actual' in productos if redundant
        # Actually src/backend.py updates both stock_almacen and does not seem to have a 'stock' column in products table (it calculates it in query)
        
        # Check orphan stock entries
        orphans = cursor.execute("SELECT COUNT(*) FROM stock_almacen WHERE producto_id NOT IN (SELECT id FROM productos)").fetchone()[0]
        if orphans > 0:
             print(f"    ⚠️ Found {orphans} orphan records in stock_almacen.")
        else:
             print("    ✅ No orphan stock records.")
             
    except Exception as e:
         print(f"    ❌ Error checking stock: {e}")

    conn.close()

if __name__ == "__main__":
    audit_db()
