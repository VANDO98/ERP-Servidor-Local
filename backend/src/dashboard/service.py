
import sqlite3
import pandas as pd
from src.database.db import get_connection
from src.shared.external_api import obtener_tc_sunat
from src.inventory.service import calcular_valorizado_fifo # Import FIFO logic directly?
# FIFO logic is complex and in inventory service. It's better to reuse it or replicate basic approximation.
# Reusing is better for consistency.

def obtener_kpis_dashboard(start_date, end_date):
    """Calcula KPIs principales: Compras, Inventario, Docs, TC"""
    conn = get_connection()
    tc = obtener_tc_sunat()
    
    try:
        # 1. Total Compras
        query_compras = f"""
            SELECT TOTAL(
                CASE 
                    WHEN moneda = 'USD' THEN total_compra * COALESCE(tipo_cambio, {tc})
                    ELSE total_compra
                END
            ) as monto, 
            COUNT(*) as docs
            FROM compras_cabecera
            WHERE fecha_emision BETWEEN ? AND ?
        """
        cursor = conn.cursor()
        cursor.execute(query_compras, (start_date, end_date))
        res_compras = cursor.fetchone()
        monto_compras = res_compras[0] if res_compras[0] else 0.0
        docs_compras = res_compras[1] if res_compras[1] else 0

        # 1.1 Total Salidas (Valorizado)
        # Calculate outputs value based on cost average at the moment or current cost?
        # Simpler: Subtotal from salidas_detalle not usually stored, we calc on fly
        # Or check if we have total in salidas_cabecera? No.
        # Let's sum quantity * current average cost (approx) or price
        # Better: SUM(sd.cantidad * p.precio_venta) as 'Ventas Estimadas' OR
        # SUM(sd.cantidad * p.costo_promedio) as 'Costo Salidas'
        # KPI usually implies Revenue or Cost. Let's do Cost for now as it's inventory mgmt,
        # OR Revenue if it's a "Sales" dashboard. 
        # Label says "Salidas Totales" and icon is TrendingUp (Sales-like).
        # Let's use PRECIO VENTA for "Ventas/Salidas" value.
        
        query_salidas = """
            SELECT TOTAL(sd.cantidad * p.precio_venta) as monto
            FROM salidas_detalle sd
            JOIN salidas_cabecera sc ON sd.salida_id = sc.id
            JOIN productos p ON sd.producto_id = p.id
            WHERE sc.fecha BETWEEN ? AND ?
        """
        cursor.execute(query_salidas, (start_date, end_date))
        monto_salidas = cursor.fetchone()[0] or 0.0

        # 2. Valor del Inventario (Optimized: Use Costo Promedio per product instead of slow FIFO)
        # FIFO calc is too heavy for dashboard load (O(N*M)).
        # We use standard Average Cost valuation for the dashboard KPI.
        try:
            cursor.execute("SELECT TOTAL(stock_actual * costo_promedio) FROM productos WHERE stock_actual > 0")
            valor_inv = cursor.fetchone()[0] or 0.0
        except Exception as e:
            print(f"Error calculating Inventory Value: {e}")
            valor_inv = 0.0

        # 3. Stock Crítico Count
        cursor.execute("SELECT COUNT(*) FROM productos WHERE stock_minimo > 0 AND stock_actual <= stock_minimo")
        stock_critico_count = cursor.fetchone()[0]

    except Exception as e:
        print(f"Error calculando KPIs: {e}")
        monto_compras = 0.0
        monto_salidas = 0.0
        docs_compras = 0
        valor_inv = 0.0
        stock_critico_count = 0
    finally:
        conn.close()

    return {
        'compras_monto': monto_compras,
        'salidas_monto': monto_salidas,
        'compras_docs': docs_compras,
        'valor_inventario': valor_inv,
        'stock_critico_count': stock_critico_count,
        'tc': tc
    }

def obtener_top_proveedores(start_date, end_date, top_n=10):
    conn = get_connection()
    tc = obtener_tc_sunat()
    query = f"""
        SELECT p.razon_social as Proveedor, 
               TOTAL(
                   CASE 
                       WHEN c.moneda = 'USD' THEN c.total_compra * COALESCE(c.tipo_cambio, {tc})
                       ELSE c.total_compra
                   END
               ) as Monto
        FROM compras_cabecera c
        JOIN proveedores p ON c.proveedor_id = p.id
        WHERE c.fecha_emision BETWEEN ? AND ?
        GROUP BY p.id, p.razon_social
        ORDER BY Monto DESC
        LIMIT {int(top_n)}
    """
    try:
        df = pd.read_sql(query, conn, params=(start_date, end_date))
        return df
    finally:
        conn.close()

def obtener_gastos_por_categoria(start_date, end_date):
    conn = get_connection()
    tc = obtener_tc_sunat()
    query = f"""
        SELECT cat.nombre as Categoria, 
               TOTAL(
                   CASE 
                       WHEN cc.moneda = 'USD' THEN cd.subtotal * COALESCE(cc.tipo_cambio, {tc})
                       ELSE cd.subtotal
                   END
               ) as Monto
        FROM compras_detalle cd
        JOIN compras_cabecera cc ON cd.compra_id = cc.id
        JOIN productos p ON cd.producto_id = p.id
        JOIN categorias cat ON p.categoria_id = cat.id
        WHERE cc.fecha_emision BETWEEN ? AND ?
        GROUP BY cat.nombre
        ORDER BY Monto DESC
    """
    try:
        df = pd.read_sql(query, conn, params=(start_date, end_date))
        return df
    finally:
        conn.close()

def obtener_evolucion_compras(start_date, end_date):
    conn = get_connection()
    tc = obtener_tc_sunat()
    query = f"""
        SELECT fecha_emision as Fecha, 
               TOTAL(
                   CASE 
                       WHEN moneda = 'USD' THEN total_compra * COALESCE(tipo_cambio, {tc})
                       ELSE total_compra
                   END
               ) as Monto, 
               COUNT(*) as Cantidad
        FROM compras_cabecera
        WHERE fecha_emision BETWEEN ? AND ?
        GROUP BY fecha_emision
        ORDER BY fecha_emision
    """
    try:
        df = pd.read_sql(query, conn, params=(start_date, end_date))
        if not df.empty:
            df['Fecha'] = pd.to_datetime(df['Fecha'])
        return df
    finally:
        conn.close()

def obtener_alertas_criticas():
    conn = get_connection()
    cursor = conn.cursor()
    
    alertas = {
        'sin_stock': {'count': 0, 'items': []},
        'sin_movimiento': {'count': 0, 'items': []},
        'compras_grandes': {'count': 0, 'items': []},
        'facturas_duplicadas': {'count': 0, 'items': []}
    }
    
    try:
        # 1. Sin Stock
        cursor.execute("SELECT nombre, stock_actual, stock_minimo, unidad_medida FROM productos WHERE stock_actual <= 0")
        rows = cursor.fetchall()
        alertas['sin_stock']['items'] = [{'nombre': r[0], 'stock': r[1], 'min': r[2], 'um': r[3]} for r in rows]
        alertas['sin_stock']['count'] = len(rows)
        
        # 2. Sin Movimiento (> 90 days)
        cursor.execute("""
            SELECT p.nombre, MAX(s.fecha) as ultima_salida
            FROM productos p
            LEFT JOIN salidas_detalle sd ON p.id = sd.producto_id
            LEFT JOIN salidas_cabecera s ON sd.salida_id = s.id
            WHERE p.stock_actual > 0
            GROUP BY p.id
            HAVING (MAX(s.fecha) < date('now', '-90 days')) OR (MAX(s.fecha) IS NULL)
        """)
        rows = cursor.fetchall()
        alertas['sin_movimiento']['items'] = [{'nombre': r[0], 'ultimo_movimiento': r[1] if r[1] else 'Nunca'} for r in rows]
        alertas['sin_movimiento']['count'] = len(rows)
        
        # 3. Compras Grandes
        cursor.execute("""
            SELECT c.serie || '-' || c.numero, p.razon_social, c.fecha_emision,
                   CASE WHEN c.moneda = 'USD' THEN c.total_compra * COALESCE(c.tipo_cambio, 3.75) ELSE c.total_compra END as monto_pen
            FROM compras_cabecera c
            JOIN proveedores p ON c.proveedor_id = p.id
            WHERE c.fecha_emision >= date('now', '-7 days') AND monto_pen > 10000
        """)
        rows = cursor.fetchall()
        alertas['compras_grandes']['items'] = [{'documento': r[0], 'proveedor': r[1], 'fecha': r[2], 'monto': r[3]} for r in rows]
        alertas['compras_grandes']['count'] = len(rows)
        
        # 4. Duplicados
        cursor.execute("""
            SELECT p.razon_social, c.fecha_emision, c.total_compra, COUNT(*) as cnt
            FROM compras_cabecera c
            JOIN proveedores p ON c.proveedor_id = p.id
            GROUP BY c.proveedor_id, c.fecha_emision, c.total_compra
            HAVING cnt > 1
        """)
        rows = cursor.fetchall()
        alertas['facturas_duplicadas']['items'] = [{'proveedor': r[0], 'fecha': r[1], 'monto': r[2], 'cantidad': r[3]} for r in rows]
        alertas['facturas_duplicadas']['count'] = len(rows)
        
    except Exception as e:
        print(f"Error alertas: {e}")
    finally:
        conn.close()
    
    return alertas
