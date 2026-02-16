
import sqlite3
import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database.db import get_connection

def verify_integrity():
    print("--- STARTING DEEP INTEGRITY CHECK ---")
    conn = get_connection()
    cursor = conn.cursor()
    
    issues = []

    try:
        # 1. Check Stock Consistency (Productos vs Stock Almacen)
        print("1. Checking Stock Consistency...")
        cursor.execute("""
            SELECT p.id, p.nombre, p.stock_actual, SUM(sa.stock_actual)
            FROM productos p
            LEFT JOIN stock_almacen sa ON p.id = sa.producto_id
            GROUP BY p.id
            HAVING ABS(p.stock_actual - COALESCE(SUM(sa.stock_actual), 0)) > 0.001
        """)
        rows = cursor.fetchall()
        if rows:
            for r in rows:
                issues.append(f"[STOCK_MISMATCH] Product {r[1]} (ID:{r[0]}): Main Stock={r[2]}, Almacen Sum={r[3]}")
        
        # 2. Check Orphaned Details (Compras)
        print("2. Checking Orphaned Purchase Details...")
        cursor.execute("""
            SELECT COUNT(*) FROM compras_detalle 
            WHERE compra_id NOT IN (SELECT id FROM compras_cabecera)
        """)
        cnt = cursor.fetchone()[0]
        if cnt > 0:
            issues.append(f"[ORPHAN_RECORDS] Found {cnt} orphaned rows in compras_detalle")

        # 3. Check Orphaned Details (Salidas)
        print("3. Checking Orphaned Output Details...")
        cursor.execute("""
            SELECT COUNT(*) FROM salidas_detalle 
            WHERE salida_id NOT IN (SELECT id FROM salidas_cabecera)
        """)
        cnt = cursor.fetchone()[0]
        if cnt > 0:
            issues.append(f"[ORPHAN_RECORDS] Found {cnt} orphaned rows in salidas_detalle")

        # 4. Check Negative Stock
        print("4. Checking Negative Stock...")
        cursor.execute("SELECT nombre, stock_actual FROM productos WHERE stock_actual < 0")
        rows = cursor.fetchall()
        for r in rows:
            issues.append(f"[NEGATIVE_STOCK] Product {r[0]} has negative stock: {r[1]}")

        # 5. Check Null References in Critical Fields
        print("5. Checking Null Critical References...")
        cursor.execute("SELECT COUNT(*) FROM compras_cabecera WHERE proveedor_id IS NULL")
        if cursor.fetchone()[0] > 0:
            issues.append("[DATA_INTEGRITY] Found purchases without provider_id")

    except Exception as e:
        issues.append(f"[EXECUTION_ERROR] {str(e)}")
    finally:
        conn.close()

    print("\n--- VALIDATION RESULTS ---")
    if not issues:
        print("✅ NO CRITICAL ISSUES FOUND. SYSTEM INTEGRITY IS GOOD.")
    else:
        print(f"⚠️ FOUND {len(issues)} ISSUES:")
        for i in issues:
            print(f"  - {i}")
    print("--------------------------")

if __name__ == "__main__":
    verify_integrity()
