"""
Backend Dashboard Adapter - Funciones para compatibilidad con Dash
Implementa funciones de analítica para el dashboard y wrappers para el backend original.
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

# Definir ruta de BD hardcoded o relativa robusta para evitar problemas de import
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def get_connection():
    """Retorna conexión a la base de datos"""
    return sqlite3.connect(DB_PATH)

# --- Funciones de Analítica (Dashboard) ---

def obtener_tipo_cambio_actual():
    """Retorna T.C. simulado o real"""
    return 3.75

def obtener_kpis_dashboard(start_date, end_date):
    """Calcula KPIs principales: Compras, Inventario, Docs, TC"""
    conn = get_connection()
    
    try:
        # 1. Total Compras en el periodo
        query_compras = """
            SELECT TOTAL(total_final) as monto, COUNT(*) as docs
            FROM compras_cabecera
            WHERE fecha BETWEEN ? AND ?
        """
        cursor = conn.cursor()
        cursor.execute(query_compras, (start_date, end_date))
        res_compras = cursor.fetchone()
        monto_compras = res_compras[0] if res_compras[0] else 0.0
        docs_compras = res_compras[1] if res_compras[1] else 0

        # 2. Valor del Inventario (Actual)
        query_inv = """
            SELECT TOTAL(p.costo_promedio * COALESCE(sa.stock_actual, 0))
            FROM productos p
            LEFT JOIN stock_almacen sa ON p.id = sa.producto_id
        """
        cursor.execute(query_inv)
        valor_inv = cursor.fetchone()[0]

    except Exception as e:
        print(f"Error calculando KPIs: {e}")
        monto_compras = 0.0
        docs_compras = 0
        valor_inv = 0.0
    finally:
        conn.close()

    return {
        'compras_monto': monto_compras,
        'compras_docs': docs_compras,
        'valor_inventario': valor_inv,
        'tc': obtener_tipo_cambio_actual()
    }

def obtener_top_proveedores(start_date, end_date, top_n=10):
    """Retorna DF con top proveedores por monto de compra"""
    conn = get_connection()
    query = f"""
        SELECT p.razon_social as Proveedor, TOTAL(c.total_final) as Monto
        FROM compras_cabecera c
        JOIN proveedores p ON c.proveedor_id = p.id
        WHERE c.fecha BETWEEN ? AND ?
        GROUP BY p.id, p.razon_social
        ORDER BY Monto DESC
        LIMIT ?
    """
    df = pd.read_sql(query, conn, params=(start_date, end_date, top_n))
    conn.close()
    return df

def obtener_gastos_por_categoria(start_date, end_date):
    """Retorna DF con gastos agrupados por categoría"""
    conn = get_connection()
    query = """
        SELECT cat.nombre as Categoria, TOTAL(cd.subtotal) as Monto
        FROM compras_detalle cd
        JOIN compras_cabecera cc ON cd.compra_id = cc.id
        JOIN productos p ON cd.producto_id = p.id
        JOIN categorias cat ON p.categoria_id = cat.id
        WHERE cc.fecha BETWEEN ? AND ?
        GROUP BY cat.nombre
        ORDER BY Monto DESC
    """
    df = pd.read_sql(query, conn, params=(start_date, end_date))
    conn.close()
    return df

def obtener_evolucion_compras(start_date, end_date):
    """Retorna DF con evolución diaria/mensual de compras"""
    conn = get_connection()
    query = """
        SELECT fecha as Fecha, TOTAL(total_final) as Monto, COUNT(*) as Cantidad
        FROM compras_cabecera
        WHERE fecha BETWEEN ? AND ?
        GROUP BY fecha
        ORDER BY fecha
    """
    df = pd.read_sql(query, conn, params=(start_date, end_date))
    conn.close()
    
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
    return df

def obtener_info_producto(producto_id):
    """Retorna dict con info de stock y costos de un producto"""
    conn = get_connection()
    
    query_prod = """
        SELECT p.costo_promedio, TOTAL(sa.stock_actual)
        FROM productos p
        LEFT JOIN stock_almacen sa ON p.id = sa.producto_id
        WHERE p.id = ?
        GROUP BY p.id
    """
    cursor = conn.cursor()
    cursor.execute(query_prod, (producto_id,))
    row = cursor.fetchone()
    
    costo = row[0] if row else 0.0
    stock = row[1] if row else 0.0
    
    query_ult = """
        SELECT MAX(cc.fecha)
        FROM compras_detalle cd
        JOIN compras_cabecera cc ON cd.compra_id = cc.id
        WHERE cd.producto_id = ?
    """
    cursor.execute(query_ult, (producto_id,))
    ult_fecha = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'stock_actual': stock,
        'costo_promedio': costo,
        'valor_total': stock * costo,
        'ultima_compra': ult_fecha if ult_fecha else "N/A"
    }

def obtener_kardex_producto(producto_id, start_date=None, end_date=None):
    """Retorna DF con movimientos (Kardex)"""
    conn = get_connection()
    
    params = []
    where_clause = ""
    if start_date and end_date:
        where_clause = " AND fecha BETWEEN ? AND ?"
        params = [producto_id, start_date, end_date, producto_id, start_date, end_date]
    else:
        params = [producto_id, producto_id]

    query = f"""
        SELECT 
            cc.fecha as Fecha, 
            'COMPRA' as TipoMovimiento, 
            cc.numero_documento as Documento,
            cd.cantidad as Entradas,
            0 as Salidas
        FROM compras_detalle cd
        JOIN compras_cabecera cc ON cd.compra_id = cc.id
        WHERE cd.producto_id = ? {where_clause.replace('fecha', 'cc.fecha')}
        
        UNION ALL
        
        SELECT 
            sc.fecha as Fecha, 
            'SALIDA' as TipoMovimiento, 
            'Salida #' || sc.id as Documento,
            0 as Entradas,
            sd.cantidad as Salidas
        FROM salidas_detalle sd
        JOIN salidas_cabecera sc ON sd.salida_id = sc.id
        WHERE sd.producto_id = ? {where_clause.replace('fecha', 'sc.fecha')}
        
        ORDER BY Fecha ASC
    """
    
    columns = ['Fecha', 'TipoMovimiento', 'Documento', 'Entradas', 'Salidas']
    data = []
    
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        for r in rows:
            data.append(r)
    except Exception as e:
        print(f"Error kardex: {e}")
        
    df = pd.DataFrame(data, columns=columns)
    
    if not df.empty:
        df['Saldo'] = (df['Entradas'] - df['Salidas']).cumsum()
    else:
        df['Saldo'] = 0
        
    conn.close()
    return df

# --- Funciones CRUD Wrappers ---

def obtener_proveedores():
    conn = get_connection()
    df = pd.read_sql("SELECT id, razon_social FROM proveedores", conn)
    conn.close()
    return list(df.itertuples(index=False, name=None))

def obtener_proveedores_completo():
    conn = get_connection()
    df = pd.read_sql("SELECT id, ruc_dni as RUC, razon_social as RazonSocial FROM proveedores", conn)
    conn.close()
    return list(df.itertuples(index=False, name=None))

def obtener_productos():
    conn = get_connection()
    df = pd.read_sql("SELECT id, nombre FROM productos", conn)
    conn.close()
    return list(df.itertuples(index=False, name=None))

def obtener_productos_completo():
    conn = get_connection()
    query = """
        SELECT p.id, p.nombre, c.nombre as categoria, p.unidad_medida, 
               COALESCE(SUM(sa.stock_actual), 0) as stock
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        LEFT JOIN stock_almacen sa ON p.id = sa.producto_id
        GROUP BY p.id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return list(df.itertuples(index=False, name=None))

def obtener_categorias():
    conn = get_connection()
    df = pd.read_sql("SELECT id, nombre FROM categorias", conn)
    conn.close()
    return list(df.itertuples(index=False, name=None))

def registrar_orden_compra(proveedor_id, fecha, moneda, items):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO ordenes_compra (proveedor_id, fecha_emision, fecha_entrega_est, estado, moneda, observaciones)
            VALUES (?, ?, ?, 'PENDIENTE', ?, '')
        """, (proveedor_id, fecha, fecha, moneda))
        oc_id = cursor.lastrowid
        
        for item in items:
            prod_nombre = item['Producto']
            cursor.execute("SELECT id FROM productos WHERE nombre = ?", (prod_nombre,))
            res_prod = cursor.fetchone()
            if not res_prod:
                raise Exception(f"Producto no encontrado: {prod_nombre}")
            
            pid = res_prod[0]
            qty = float(item['Cantidad'])
            price = float(item['PrecioUnitario'])
            
            cursor.execute("""
                INSERT INTO ordenes_compra_det (oc_id, producto_id, cantidad_solicitada, precio_unitario_pactado)
                VALUES (?, ?, ?, ?)
            """, (oc_id, pid, qty, price))
            
        conn.commit()
        return {'success': True, 'orden_id': oc_id}
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

# --- Funciones de Compras (Facturas) y CRUD Data Entry ---

def registrar_compra(cabecera, detalles):
    """
    Registra una compra (factura) completa: Cabecera + Detalles + Actualización Stock/Costo
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Insertar Cabecera
        cursor.execute("""
            INSERT INTO compras_cabecera (proveedor_id, fecha, numero_documento, tipo_documento, moneda, total_final, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            cabecera['proveedor_id'], 
            cabecera['fecha'], 
            cabecera['numero_documento'], 
            cabecera.get('tipo_documento', 'FACTURA'),
            cabecera['moneda'], 
            cabecera['total'], 
            cabecera.get('observaciones', '')
        ))
        compra_id = cursor.lastrowid
        
        # 2. Detalles y Actualización Stock/Costo
        tc = 3.75 # TC Fijo o lookup
        
        for d in detalles:
            # Buscar ID si viene nombre
            if 'pid' not in d and 'Producto' in d:
                cursor.execute("SELECT id FROM productos WHERE nombre = ?", (d['Producto'],))
                res = cursor.fetchone()
                if not res: raise Exception(f"Producto {d['Producto']} no encontrado")
                pid = res[0]
            else:
                pid = d['pid']
                
            qty = float(d['cantidad']) if 'cantidad' in d else float(d['Cantidad'])
            # Precio unitario
            if 'precio_unitario' in d: precio_orig = float(d['precio_unitario'])
            elif 'PrecioUnitario' in d: precio_orig = float(d['PrecioUnitario'])
            else: precio_orig = 0.0
            
            # Total linea
            if 'total' in d: total_linea = float(d['total']) 
            elif 'Total' in d: total_linea = float(d['Total'])
            else: total_linea = qty * precio_orig
            
            # Convertir precio a PEN para costo promedio
            precio_pen = precio_orig * tc if cabecera['moneda'] == 'USD' else precio_orig
            
            # Obtener datos actuales del producto
            cursor.execute("SELECT costo_promedio FROM productos WHERE id = ?", (pid,))
            row_prod = cursor.fetchone()
            costo_ant = row_prod[0] if row_prod else 0.0
            
            # Obtener stock actual (global o almacen 1)
            almacen_id = 1
            cursor.execute("SELECT id, stock_actual FROM stock_almacen WHERE producto_id = ? AND almacen_id = ?", (pid, almacen_id))
            row_stock = cursor.fetchone()
            
            stock_ant = 0
            stock_id = None
            if row_stock:
                stock_id, stock_ant = row_stock
            
            # Calcular Nuevo Costo Promedio PONDERADO
            nuevo_stock = stock_ant + qty
            if nuevo_stock > 0:
                nuevo_costo = ((stock_ant * costo_ant) + (qty * precio_pen)) / nuevo_stock
            else:
                nuevo_costo = precio_pen
                
            # Insertar Detalle
            cursor.execute("""
                INSERT INTO compras_detalle (compra_id, producto_id, descripcion, unidad_medida, cantidad, precio_unitario, subtotal, costo_previo, tasa_impuesto)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                compra_id, pid, d.get('descripcion', ''), d.get('unidad', 'UND'),
                qty, precio_orig, total_linea, costo_ant, 18.0
            ))
            
            # Actualizar Stock
            if stock_id:
                cursor.execute("UPDATE stock_almacen SET stock_actual = ? WHERE id = ?", (nuevo_stock, stock_id))
            else:
                cursor.execute("INSERT INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, ?, ?)", (pid, almacen_id, qty))
            
            # Actualizar Costo Promedio
            cursor.execute("UPDATE productos SET costo_promedio = ? WHERE id = ?", (nuevo_costo, pid))
            
        conn.commit()
        return {'success': True, 'compra_id': compra_id}
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def obtener_compras_historial():
    """Retorna historial de cabeceras de compra"""
    conn = get_connection()
    query = """
        SELECT 
            c.id, 
            c.fecha, 
            c.numero_documento, 
            p.razon_social as proveedor, 
            c.moneda, 
            c.total_final,
            (SELECT COUNT(*) FROM compras_detalle WHERE compra_id = c.id) as items
        FROM compras_cabecera c
        JOIN proveedores p ON c.proveedor_id = p.id
        ORDER BY c.fecha DESC, c.id DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return list(df.itertuples(index=False, name=None))

def obtener_compras_detalle_historial():
    """Retorna historial detallado de items comprados"""
    conn = get_connection()
    query = """
        SELECT 
            c.fecha,
            c.numero_documento,
            p.razon_social as proveedor,
            prod.nombre as producto,
            cd.cantidad,
            cd.precio_unitario,
            cd.subtotal,
            c.moneda,
            c.id as compra_id
        FROM compras_detalle cd
        JOIN compras_cabecera c ON cd.compra_id = c.id
        JOIN proveedores p ON c.proveedor_id = p.id
        JOIN productos prod ON cd.producto_id = prod.id
        ORDER BY c.fecha DESC, c.id DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return list(df.itertuples(index=False, name=None))

# Funciones de creación (CRUD)
def crear_proveedor(ruc, razon_social, direccion, telefono, email, contacto):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if exists
        cursor.execute("SELECT id FROM proveedores WHERE ruc_dni = ?", (ruc,))
        if cursor.fetchone():
            return False, "RUC ya registrado"
            
        cursor.execute("INSERT INTO proveedores (ruc_dni, razon_social, direccion, telefono, email, contacto) VALUES (?, ?, ?, ?, ?, ?)",
                       (ruc, razon_social, direccion, telefono, email, contacto))
        conn.commit()
        return True, "Proveedor registrado exitosamente"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def crear_categoria(nombre):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (nombre,))
        if cursor.fetchone():
            return False, "Categoría ya existe"
            
        cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre,))
        conn.commit()
        return True, "Categoría creada"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def crear_producto(sku, nombre, unidad, categoria_id, stock_inicial=0):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM productos WHERE nombre = ?", (nombre,))
        if cursor.fetchone():
            return False, "Producto ya existe con ese nombre", None
            
        cursor.execute("INSERT INTO productos (codigo_sku, nombre, unidad_medida, categoria_id, costo_promedio) VALUES (?, ?, ?, ?, 0)",
                       (sku, nombre, unidad, categoria_id))
        pid = cursor.lastrowid
        
        # Stock inicial
        if stock_inicial > 0:
             cursor.execute("INSERT INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, 1, ?)", (pid, stock_inicial))
             
        conn.commit()
        return True, "Producto creado", pid
    except Exception as e:
        return False, f"Error: {str(e)}", None
    finally:
        conn.close()
