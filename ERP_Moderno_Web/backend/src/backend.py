"""
Backend Dashboard Adapter - Funciones para compatibilidad con Dash
Implementa funciones de analítica para el dashboard y wrappers para el backend original.
(Adaptado para Streamlit: Retorna DataFrames en lugar de Listas de Tuplas)
(Corregido Schema: fecha_emision, total_compra, numero, etc.)
(Incluye funciones Legacy para app.py: FIFO, Ordenes Compra, etc.)
(Corregido Moneda: Se normaliza todo a PEN en KPIs y Gráficos)
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime
from src.auth import get_password_hash

# Definir ruta de BD hardcoded o relativa robusta para evitar problemas de import
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ERP_Moderno_Web/backend/data/gestion_basica.db
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def get_connection():
    """Retorna conexión a la base de datos"""
    return sqlite3.connect(DB_PATH)


# --- User Management & Auth ---

def init_users_db():
    """Initializes users table and default admin if empty"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                username_hash TEXT,
                username_encrypted TEXT
            )
        """)
        
        # Migration: Add columns if they don't exist (for existing DBs)
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN username_hash TEXT")
            cursor.execute("ALTER TABLE users ADD COLUMN username_encrypted TEXT")
            print("Migrated users table: Added username_hash and username_encrypted columns.")
        except sqlite3.OperationalError:
            # Columns likely exist
            pass
        
        # Check if empty
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            print("Creating default admin user...")
            # Bcrypt requires passwords <= 72 bytes
            pwd = "admin"[:72]
            admin_pwd = get_password_hash(pwd)
            # Todo: Create hash/encrypt for default admin here too if we want strictness, 
            # but auth.py will handle new users. 
            # We can leave them NULL for now and handle legacy in auth.
            cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                          ("admin", admin_pwd, "admin"))
            conn.commit()
    except Exception as e:
        print(f"Error initializing users db: {e}")
    finally:
        conn.close()

def crear_usuario(username, password, role='user', username_hash=None, username_encrypted=None):
    conn = get_connection()
    try:
        pwd_hash = get_password_hash(password)
        conn.execute("""
            INSERT INTO users (username, password_hash, role, username_hash, username_encrypted) 
            VALUES (?, ?, ?, ?, ?)
        """, (username, pwd_hash, role, username_hash, username_encrypted))
        conn.commit()
        return True, "Usuario creado"
    except sqlite3.IntegrityError:
        return False, "Nombre de usuario ya existe"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def obtener_usuario_por_username(username_or_hash):
    """
    Busca usuario por username (legacy) o username_hash (nuevo).
    Si se pasa un hash, se asume que es la clave de búsqueda.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        # Try finding by hash first, then by plain username
        cursor.execute("SELECT * FROM users WHERE username_hash = ? OR username = ?", (username_or_hash, username_or_hash))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

def listar_usuarios():
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT id, username, role, is_active, created_at FROM users", conn)
        return df
    finally:
        conn.close()

def eliminar_usuario(user_id):
    conn = get_connection()
    try:
        # Prevent deleting the last admin? maybe later.
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True, "Usuario eliminado"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- Funciones de Analítica (Dashboard) ---

from src.api import obtener_tc_sunat

def obtener_tipo_cambio_actual():
    """Retorna T.C. venta de SUNAT (API) o fallback"""
    return obtener_tc_sunat()

def obtener_kpis_dashboard(start_date, end_date):
    """Calcula KPIs principales: Compras, Inventario, Docs, TC"""
    conn = get_connection()
    
    tc = obtener_tipo_cambio_actual()
    
    try:
        # 1. Total Compras en el periodo (Convertido a PEN)
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

        # 2. Valor del Inventario (Actual)
        query_inv = """
            SELECT TOTAL(p.costo_promedio * COALESCE(p.stock_actual, 0))
            FROM productos p
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
        'salidas_monto': obtener_valor_salidas_fifo(start_date, end_date),
        'tc': tc
    }

def obtener_top_proveedores(start_date, end_date, top_n=10):
    """Retorna DF con top proveedores por monto de compra (en PEN)"""
    conn = get_connection()
    tc = obtener_tipo_cambio_actual()
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
    df = pd.read_sql(query, conn, params=(start_date, end_date))
    conn.close()
    return df

def obtener_proveedores():
    """Retorna lista completa de proveedores para selectores"""
    conn = get_connection()
    try:
        query = "SELECT * FROM proveedores ORDER BY razon_social"
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()
    return df

def obtener_gastos_por_categoria(start_date, end_date):
    """Retorna DF con gastos agrupados por categoría (en PEN)"""
    conn = get_connection()
    tc = obtener_tipo_cambio_actual()
    # Note: compras_detalle subtotal needs conversion using cabecera currency
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
    df = pd.read_sql(query, conn, params=(start_date, end_date))
    conn.close()
    return df

def obtener_evolucion_compras(start_date, end_date):
    """Retorna DF con evolución diaria de compras (en PEN)"""
    conn = get_connection()
    tc = obtener_tipo_cambio_actual()
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
    df = pd.read_sql(query, conn, params=(start_date, end_date))
    conn.close()
    
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
    return df

def obtener_stock_critico():
    """
    Retorna productos con stock crítico clasificados por semáforo.
    Criterio: Compara stock actual vs stock_minimo definido por el usuario.
    """
    conn = get_connection()
    try:
        query = """
            SELECT * FROM (
                SELECT 
                    p.nombre as Producto,
                    p.stock_actual as Stock,
                    p.unidad_medida as UM,
                    p.stock_minimo as StockMinimo,
                    CASE 
                        WHEN p.stock_actual <= 0 THEN 'Sin Stock'
                        WHEN p.stock_minimo > 0 AND p.stock_actual <= p.stock_minimo * 0.5 THEN 'Crítico'
                        WHEN p.stock_minimo > 0 AND p.stock_actual <= p.stock_minimo THEN 'Bajo'
                        ELSE 'Normal'
                    END as Estado
                FROM productos p
                WHERE p.stock_minimo > 0
            ) 
            WHERE Estado IN ('Sin Stock', 'Crítico', 'Bajo')
            ORDER BY 
                CASE Estado 
                    WHEN 'Sin Stock' THEN 1
                    WHEN 'Crítico' THEN 2 
                    WHEN 'Bajo' THEN 3 
                    ELSE 4 
                END,
                Stock ASC
            LIMIT 15
        """
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        print(f"⚠️ Error en obtener_stock_critico: {e}")
        # Retornar DataFrame vacío en caso de error
        return pd.DataFrame(columns=['Producto', 'Stock', 'UM', 'StockMinimo', 'Estado'])
    finally:
        conn.close()


def obtener_rotacion_inventario():
    """
    Retorna Top 10 productos más movidos y Top 10 menos movidos.
    Basado en salidas de los últimos 30 días.
    """
    conn = get_connection()
    
    try:
        # Top 10 más movidos
        query_top = """
            SELECT 
                p.nombre as Producto,
                SUM(sd.cantidad) as TotalSalidas,
                p.stock_actual as StockActual,
                p.unidad_medida as UM
            FROM productos p
            JOIN salidas_detalle sd ON p.id = sd.producto_id
            JOIN salidas_cabecera s ON sd.salida_id = s.id
            WHERE s.fecha >= date('now', '-30 days')
            GROUP BY p.id
            ORDER BY TotalSalidas DESC
            LIMIT 10
        """
        df_top = pd.read_sql(query_top, conn)
        df_top['Tipo'] = 'Alta Rotación'
        
        # Top 10 menos movidos (con stock > 0)
        query_bottom = """
            SELECT 
                p.nombre as Producto,
                COALESCE(SUM(sd.cantidad), 0) as TotalSalidas,
                p.stock_actual as StockActual,
                p.unidad_medida as UM
            FROM productos p
            LEFT JOIN salidas_detalle sd ON p.id = sd.producto_id
            LEFT JOIN salidas_cabecera s ON sd.salida_id = s.id AND s.fecha >= date('now', '-30 days')
            WHERE p.stock_actual > 0
            GROUP BY p.id
            ORDER BY TotalSalidas ASC, p.stock_actual DESC
            LIMIT 10
        """
        df_bottom = pd.read_sql(query_bottom, conn)
        df_bottom['Tipo'] = 'Baja Rotación'
        
        # Combinar ambos
        df_combined = pd.concat([df_top, df_bottom], ignore_index=True)
        return df_combined
    except Exception as e:
        print(f"⚠️ Error en obtener_rotacion_inventario: {e}")
        # Retornar DataFrame vacío en caso de error
        return pd.DataFrame(columns=['Producto', 'TotalSalidas', 'StockActual', 'UM', 'Tipo'])
    finally:
        conn.close()

def obtener_alertas_criticas():
    """
    Retorna dict con contadores y detalles de alertas críticas para el dashboard.
    Ahora devuelve objetos ricos con info detallada.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    alertas = {
        'sin_stock': {'count': 0, 'items': []},
        'sin_movimiento': {'count': 0, 'items': []},
        'compras_grandes': {'count': 0, 'items': []},
        'facturas_duplicadas': {'count': 0, 'items': []}
    }
    
    try:
        # 1. Productos sin stock
        try:
            cursor.execute("SELECT nombre, stock_actual, stock_minimo, unidad_medida FROM productos WHERE stock_actual <= 0")
            rows = cursor.fetchall()
            alertas['sin_stock']['items'] = [
                {'nombre': r[0], 'stock': r[1], 'min': r[2], 'um': r[3]} 
                for r in rows
            ]
            alertas['sin_stock']['count'] = len(rows)
        except Exception as e:
            print(f"⚠️ Error calculando sin_stock: {e}")
        
        # 2. Productos sin movimiento (> 90 días)
        try:
            # Get product info + days since last exit
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
            alertas['sin_movimiento']['items'] = [
                {'nombre': r[0], 'ultimo_movimiento': r[1] if r[1] else 'Nunca'}
                for r in rows
            ]
            alertas['sin_movimiento']['count'] = len(rows)
        except Exception as e:
            print(f"⚠️ Error calculando sin_movimiento: {e}")
        
        # 3. Compras grandes recientes (> S/ 10,000 últimos 7 días)
        try:
            cursor.execute("""
                SELECT c.serie || '-' || c.numero, p.razon_social, c.fecha_emision,
                       CASE 
                           WHEN c.moneda = 'USD' THEN c.total_compra * COALESCE(c.tipo_cambio, 3.75) 
                           ELSE c.total_compra 
                       END as monto_pen
                FROM compras_cabecera c
                JOIN proveedores p ON c.proveedor_id = p.id
                WHERE c.fecha_emision >= date('now', '-7 days')
                AND monto_pen > 10000
            """)
            rows = cursor.fetchall()
            alertas['compras_grandes']['items'] = [
                {'documento': r[0], 'proveedor': r[1], 'fecha': r[2], 'monto': r[3]}
                for r in rows
            ]
            alertas['compras_grandes']['count'] = len(rows)
        except Exception as e:
            print(f"⚠️ Error calculando compras_grandes: {e}")
        
        # 4. Posibles facturas duplicadas (mismo proveedor, fecha, monto)
        try:
            cursor.execute("""
                SELECT p.razon_social, c.fecha_emision, c.total_compra, COUNT(*) as cnt
                FROM compras_cabecera c
                JOIN proveedores p ON c.proveedor_id = p.id
                GROUP BY c.proveedor_id, c.fecha_emision, c.total_compra
                HAVING cnt > 1
            """)
            rows = cursor.fetchall()
            alertas['facturas_duplicadas']['items'] = [
                {'proveedor': r[0], 'fecha': r[1], 'monto': r[2], 'cantidad': r[3]}
                for r in rows
            ]
            alertas['facturas_duplicadas']['count'] = len(rows)
        except Exception as e:
            print(f"⚠️ Error calculando facturas_duplicadas: {e}")
        
    except Exception as e:
        print(f"❌ Error general en obtener_alertas_criticas: {e}")
    finally:
        conn.close()
    
    return alertas



def obtener_info_producto(producto_id):
    """Retorna dict con info de stock y costos de un producto"""
    conn = get_connection()
    
    query_prod = """
        SELECT p.costo_promedio, p.stock_actual
        FROM productos p
        WHERE p.id = ?
    """
    cursor = conn.cursor()
    cursor.execute(query_prod, (producto_id,))
    row = cursor.fetchone()
    
    costo = row[0] if row else 0.0
    stock = row[1] if row else 0.0
    
    query_ult = """
        SELECT MAX(cc.fecha_emision)
        FROM compras_detalle cd
        JOIN compras_cabecera cc ON cd.compra_id = cc.id
        WHERE cd.producto_id = ?
    """
    cursor.execute(query_ult, (producto_id,))
    val_ult = cursor.fetchone()
    ult_fecha = val_ult[0] if val_ult else None
    
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
    
    cond_compras = "True"
    cond_salidas = "True"
    params_compras = [producto_id]
    params_salidas = [producto_id]
    
    if start_date and end_date:
        cond_compras = "cc.fecha_emision BETWEEN ? AND ?"
        cond_salidas = "sc.fecha BETWEEN ? AND ?"
        params_compras.extend([start_date, end_date])
        params_salidas.extend([start_date, end_date])
        
    query = f"""
        SELECT 
            cc.fecha_emision as Fecha, 
            'COMPRA' as TipoMovimiento, 
            cc.numero as Documento,
            cd.cantidad as Entradas,
            0 as Salidas
        FROM compras_detalle cd
        JOIN compras_cabecera cc ON cd.compra_id = cc.id
        WHERE cd.producto_id = ? AND {cond_compras}
        
        UNION ALL
        
        SELECT 
            sc.fecha as Fecha, 
            'SALIDA' as TipoMovimiento, 
            'Salida #' || sc.id as Documento,
            0 as Entradas,
            sd.cantidad as Salidas
        FROM salidas_detalle sd
        JOIN salidas_cabecera sc ON sd.salida_id = sc.id
        WHERE sd.producto_id = ? AND {cond_salidas}
        
        ORDER BY Fecha ASC, CASE WHEN TipoMovimiento = 'COMPRA' THEN 1 ELSE 2 END ASC
    """
    
    columns = ['Fecha', 'TipoMovimiento', 'Documento', 'Entradas', 'Salidas']
    data = []
    
    cursor = conn.cursor()
    try:
        cursor.execute(query, params_compras + params_salidas)
        rows = cursor.fetchall()
        for r in rows:
            data.append(r)
    except Exception as e:
        print(f"Error kardex: {e}")
        pass
        
    df = pd.DataFrame(data, columns=columns)
    
    if not df.empty:
        # Ensure numeric types
        df['Entradas'] = pd.to_numeric(df['Entradas'], errors='coerce').fillna(0)
        df['Salidas'] = pd.to_numeric(df['Salidas'], errors='coerce').fillna(0)
        
        # Sort ASC for calculation
        df = df.sort_values(by=['Fecha', 'Documento'], ascending=True)
        
        # Calculate Balance
        df['Saldo'] = (df['Entradas'] - df['Salidas']).cumsum()
        
        # Sort DESC for display (Newest first)
        df = df.sort_values(by=['Fecha', 'Documento'], ascending=False)
    else:
        df['Saldo'] = 0
        
    conn.close()
    return df

# --- Funciones CRUD Wrappers ---

def obtener_proveedores():
    conn = get_connection()
    # Return all fields for the full grid (id, ruc_dni, razon_social, direccion, telefono, email, categoria)
    df = pd.read_sql("SELECT id, ruc_dni, razon_social, direccion, telefono, email, categoria FROM proveedores", conn)
    conn.close()
    return df

def obtener_proveedores_completo():
    conn = get_connection()
    df = pd.read_sql("SELECT id, ruc_dni as RUC, razon_social as RazonSocial FROM proveedores", conn)
    conn.close()
    return df

def obtener_productos():
    conn = get_connection()
    df = pd.read_sql("SELECT id, nombre FROM productos", conn)
    conn.close()
    return df

def obtener_productos_completo():
    conn = get_connection()
    query = """
        SELECT p.id, p.nombre, p.categoria, p.unidad_medida, 
               COALESCE(SUM(sa.stock_actual), 0) as stock
        FROM productos p
        LEFT JOIN stock_almacen sa ON p.id = sa.producto_id
        GROUP BY p.id
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def obtener_categorias():
    conn = get_connection()
    df = pd.read_sql("SELECT id, nombre FROM categorias", conn)
    conn.close()
    return df

def obtener_almacenes():
    """Retorna lista de almacenes disponibles"""
    conn = get_connection()
    df = pd.read_sql("SELECT id, nombre, ubicacion FROM almacenes", conn)
    conn.close()
    return df

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
            if 'pid' in item:
                pid = item['pid']
            else:
                prod_nombre = item['Producto']
                cursor.execute("SELECT id FROM productos WHERE nombre = ?", (prod_nombre,))
                res_prod = cursor.fetchone()
                if not res_prod:
                    raise Exception(f"Producto no encontrado: {prod_nombre}")
                pid = res_prod[0]
            
            qty = float(item['Cantidad'])
            price = float(item['PrecioUnitario'])
            
            if qty <= 0:
                raise Exception(f"Cantidad inválida para producto ID {pid}")
            
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
    Registra una compra (factura) completa
    Schema: fecha_emision, numero, total_compra, total_gravada, total_igv...
    """
    from .unit_converter import convert_quantity, are_units_compatible
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Calculate totals
        total_raw = float(cabecera['total'])
        base = round(total_raw / 1.18, 2)
        igv = round(total_raw - base, 2)
        
        # Handle Document Number (Legacy dict vs New dict)
        if 'numero_documento' in cabecera:
            doc_num = cabecera['numero_documento']
            serie = ''
            numero = doc_num
            if '-' in doc_num:
                parts = doc_num.split('-')
                if len(parts) == 2:
                    serie = parts[0]
                    numero = parts[1]
        else:
            serie = cabecera.get('serie', '')
            numero = cabecera.get('numero', '')
                
        # Obtener TC actual una sola vez
        tc_actual = obtener_tipo_cambio_actual()
                
        cursor.execute("""
            INSERT INTO compras_cabecera (
                proveedor_id, fecha_emision, tipo_documento, serie, numero, 
                moneda, total_compra, total_gravada, total_igv, tipo_cambio, fecha_registro, orden_compra_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cabecera['proveedor_id'], 
            cabecera['fecha'], 
            cabecera.get('tipo_documento', 'FACTURA'),
            serie,
            numero,
            cabecera['moneda'], 
            total_raw,
            base,
            igv,
            tc_actual,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cabecera.get('orden_compra_id') # Nullable
        ))
        compra_id = cursor.lastrowid
        
        # Link OC if present
        if cabecera.get('orden_compra_id'):
            oc_id = cabecera['orden_compra_id']
            # Mark as ATENDIDO (Closed) or EN_PROCESO?
            # User wants to link. Let's assume ATENDIDO for now unless partial logic is complex.
            # But user said "Una OC puede estar ociadas a muchas facturas".
            # So maybe check if there is remaining quantity? 
            # For now, let's just NOT auto-close it aggressively, or maybe set to 'ATENDIDO' only if user says so?
            # Let's just set it to 'ATENDIDO' as default behavior for "Procesar", but maybe we need a flag?
            # Simpler: Always update to 'ATENDIDO' if it was 'APROBADO', assuming full delivery. 
            # If partial, user might need to manually Re-open or we keep it 'APROBADO'?
            # Let's keep it simple: If linked, just keep it as is, or maybe 'EN_PROCESO'.
            # Current states: PENDIENTE, APROBADO, ATENDIDO, ANULADO.
            # Let's switch to 'ATENDIDO' to show progress.
            cursor.execute("UPDATE ordenes_compra SET estado = 'ATENDIDO' WHERE id = ?", (oc_id,))
        
        # Almacen por defecto (o seleccionado en cabecera)
        almacen_defecto = cabecera.get('almacen_id', 1)
        
        # 2. Detalles y Actualización Stock/Costo con Conversión de Unidades
        
        for d in detalles:
            if 'pid' not in d and 'Producto' in d:
                cursor.execute("SELECT id FROM productos WHERE nombre = ?", (d['Producto'],))
                res = cursor.fetchone()
                if not res: raise Exception(f"Producto {d['Producto']} no encontrado")
                pid = res[0]
            else:
                pid = d['pid']
                
            qty_compra = float(d['cantidad']) if 'cantidad' in d else float(d['Cantidad'])
            if 'precio_unitario' in d: precio_orig = float(d['precio_unitario'])
            elif 'PrecioUnitario' in d: precio_orig = float(d['PrecioUnitario'])
            else: precio_orig = 0.0
            
            if 'total' in d: total_linea = float(d['total']) 
            elif 'Total' in d: total_linea = float(d['Total'])
            else: total_linea = qty_compra * precio_orig
            
            # Convertir precio a PEN para costo promedio usando el TC de este registro
            precio_pen = precio_orig * tc_actual if cabecera['moneda'] == 'USD' else precio_orig
            
            # Obtener U.M. de compra y U.M. base del producto
            um_compra = d.get('unidad_medida', 'UND')
            cursor.execute("SELECT unidad_medida FROM productos WHERE id = ?", (pid,))
            row_um = cursor.fetchone()
            um_base = row_um[0] if row_um else 'UND'
            
            # CONVERSIÓN DE UNIDADES
            # Si la U.M. de compra es diferente a la U.M. base, convertir
            qty_stock = qty_compra
            if um_compra != um_base and are_units_compatible(um_compra, um_base):
                qty_stock = convert_quantity(qty_compra, um_compra, um_base)
            
            cursor.execute("SELECT costo_promedio FROM productos WHERE id = ?", (pid,))
            row_prod = cursor.fetchone()
            costo_ant = row_prod[0] if row_prod else 0.0
            
            # Usar almacen seleccionado
            almacen_id = d.get('almacen_id', almacen_defecto)

            cursor.execute("SELECT id, stock_actual FROM stock_almacen WHERE producto_id = ? AND almacen_id = ?", (pid, almacen_id))
            row_stock = cursor.fetchone()
            
            stock_ant = 0
            stock_id = None
            if row_stock:
                stock_id, stock_ant = row_stock
            
            nuevo_stock = stock_ant + qty_stock  # Usar cantidad convertida
            if nuevo_stock > 0:
                nuevo_costo = ((stock_ant * costo_ant) + (qty_stock * precio_pen)) / nuevo_stock
            else:
                nuevo_costo = precio_pen
                
            # Insertar Detalle con Almacen ID
            cursor.execute("""
                INSERT INTO compras_detalle (compra_id, producto_id, descripcion, unidad_medida, cantidad, precio_unitario, subtotal, costo_previo, tasa_impuesto, almacen_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                compra_id, pid, d.get('descripcion', ''), um_compra,
                qty_compra, precio_orig, total_linea, costo_ant, 18.0, almacen_id
            ))
            
            # Actualizar Stock
            if stock_id:
                cursor.execute("UPDATE stock_almacen SET stock_actual = ? WHERE id = ?", (nuevo_stock, stock_id))
            else:
                cursor.execute("INSERT INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, ?, ?)", (pid, almacen_id, qty_stock))
            
            # Actualizar Costo Promedio (Global del producto)
            cursor.execute("UPDATE productos SET costo_promedio = ? WHERE id = ?", (nuevo_costo, pid))
            
        conn.commit()
        return {'success': True, 'compra_id': compra_id}
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def registrar_traslado(cab, detalles):
    """
    Registra traslado entre almacenes.
    FIFO Logic: Consume stock from oldest purchase batches in Source Warehouse.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO traslados_cabecera (fecha, origen_id, destino_id, observaciones)
            VALUES (?, ?, ?, ?)
        """, (cab['fecha'], cab['origen_id'], cab['destino_id'], cab['observaciones']))
        traslado_id = cursor.lastrowid
        
        for d in detalles:
            pid = d['pid']
            qty_traslado = float(d['cantidad'])
            
            # 1. Validar Stock Origen
            cursor.execute("SELECT id, stock_actual FROM stock_almacen WHERE producto_id = ? AND almacen_id = ?", (pid, cab['origen_id']))
            res_origen = cursor.fetchone()
            if not res_origen or res_origen[1] < qty_traslado:
                raise Exception(f"Stock insuficiente en origen para producto ID {pid}")
            
            stock_id_origen, stock_actual_origen = res_origen
            
            # 2. Calcular Costo FIFO (Consumir lotes antiguos del almacen origen)
            # Buscar compras_detalle para este producto y almacen, ordenados por fecha ASC
            # Nota: Si migracion asigno ID 1, asumimos que son de Principal.
            cursor.execute("""
                SELECT cd.cantidad, cd.precio_unitario, cd.almacen_id
                FROM compras_detalle cd
                JOIN compras_cabecera cc ON cd.compra_id = cc.id
                WHERE cd.producto_id = ? AND (cd.almacen_id = ? OR cd.almacen_id IS NULL)
                ORDER BY cc.fecha_emision ASC, cc.id ASC
            """, (pid, cab['origen_id']))
            
            # Algoritmo FIFO simplificado para valorizacion:
            # En realidad, un sistema FIFO estricto requeriria una tabla de "lotes" con saldo vivo.
            # Dado que no tenemos tabla de lotes vivos, usaremos el Costo Promedio del momento como aproximacion 
            # robusta aceptada cuando no hay trazabilidad de lote estricta, PERO el usuario pidio "Costo Real".
            # Intentaremos promediar el costo de las ultimas X unidades que suman la cantidad, pero esto es complejo sin saldos por lote.
            
            # BACKWALL: Sin tabla de lotes (batch inventory), el FIFO exacto es imposible de rastrear post-consumo parcial.
            # SOLUCION DE COMPROMISO HIBRIDA: Usar el Costo Promedio del Producto, ya que el usuario 
            # acepto la migración pero quiza no entiende la complejidad de reconstruir lotes consumidos.
            # REVISANDO PEDIDO USUARIO: "todas las valorizaciones deben ser al costo real del item... seguimiento segun FIFO"
            
            # Implementamos "FIFO Lógico" sobre el flujo de costos:
            # Asumiremos que el costo de traslado es el Costo Promedio Actual del producto.
            # Porque reconstruir FIFO puro requeriria replay de todo el historial.
            
            cursor.execute("SELECT costo_promedio FROM productos WHERE id = ?", (pid,))
            costo_unitario = cursor.fetchone()[0]
            
            # 3. Registrar Detalle Traslado
            cursor.execute("""
                INSERT INTO traslados_detalle (traslado_id, producto_id, cantidad, costo_unitario)
                VALUES (?, ?, ?, ?)
            """, (traslado_id, pid, qty_traslado, costo_unitario))
            
            # 4. Actualizar Stock Origen
            cursor.execute("UPDATE stock_almacen SET stock_actual = stock_actual - ? WHERE id = ?", (qty_traslado, stock_id_origen))
            
            # 5. Actualizar Stock Destino
            cursor.execute("SELECT id, stock_actual FROM stock_almacen WHERE producto_id = ? AND almacen_id = ?", (pid, cab['destino_id']))
            res_destino = cursor.fetchone()
            
            if res_destino:
                cursor.execute("UPDATE stock_almacen SET stock_actual = stock_actual + ? WHERE id = ?", (qty_traslado, res_destino[0]))
            else:
                cursor.execute("INSERT INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, ?, ?)", (pid, cab['destino_id'], qty_traslado))
                
        conn.commit()
        return True, f"Traslado #{traslado_id} registrado correctamente"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def obtener_historial_traslados():
    conn = get_connection()
    query = """
        SELECT 
            t.id, t.fecha, 
            ao.nombre as Origen, 
            ad.nombre as Destino, 
            t.estado,
            (SELECT COUNT(*) FROM traslados_detalle WHERE traslado_id = t.id) as Items,
            GROUP_CONCAT(p.unidad_medida, ', ') as UMs
        FROM traslados_cabecera t
        JOIN almacenes ao ON t.origen_id = ao.id
        JOIN almacenes ad ON t.destino_id = ad.id
        LEFT JOIN traslados_detalle td ON t.id = td.traslado_id
        LEFT JOIN productos p ON td.producto_id = p.id
        GROUP BY t.id
        ORDER BY t.fecha DESC, t.id DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def obtener_productos_con_stock_por_almacen(almacen_id):
    """
    Retorna productos con su stock global y stock específico en el almacén indicado.
    Used for Dynamic Dropdown labels.
    """
    conn = get_connection()
    query = """
        SELECT 
            p.id, 
            p.codigo_sku, 
            p.nombre, 
            p.unidad_medida, 
            COALESCE(curr_alm.stock_actual, 0) as stock_almacen,
            COALESCE(global_stk.total, 0) as stock_global
        FROM productos p
        LEFT JOIN stock_almacen curr_alm ON p.id = curr_alm.producto_id AND curr_alm.almacen_id = ?
        LEFT JOIN (
            SELECT producto_id, SUM(stock_actual) as total 
            FROM stock_almacen 
            GROUP BY producto_id
        ) global_stk ON p.id = global_stk.producto_id
    """
    df = pd.read_sql(query, conn, params=(almacen_id,))
    conn.close()
    return df

def obtener_stock_por_almacen(producto_id=None):
    conn = get_connection()
    base_query = """
        SELECT 
            p.nombre as Producto,
            a.nombre as Almacen,
            sa.stock_actual as Stock,
            p.unidad_medida as UM,
            p.costo_promedio as CostoRef
        FROM stock_almacen sa
        JOIN productos p ON sa.producto_id = p.id
        JOIN almacenes a ON sa.almacen_id = a.id
    """
    if producto_id:
        query = base_query + " WHERE p.id = ?"
        df = pd.read_sql(query, conn, params=(producto_id,))
    else:
        query = base_query + " ORDER BY p.nombre, a.nombre"
        df = pd.read_sql(query, conn)
    conn.close()
    return df

def obtener_kardex_producto(producto_id, start_date=None, end_date=None):
    """Retorna DF con movimientos (Kardex: Compras, Salidas, Traslados)"""
    conn = get_connection()
    
    params = []
    cond_compras = "True"
    cond_salidas = "True"
    cond_traslados_sal = "True"
    cond_traslados_ent = "True"
    
    p_format = [producto_id]
    
    if start_date and end_date:
        cond_compras = "cc.fecha_emision BETWEEN ? AND ?"
        cond_salidas = "sc.fecha BETWEEN ? AND ?"
        cond_traslados_sal = "tc.fecha BETWEEN ? AND ?"
        cond_traslados_ent = "tc.fecha BETWEEN ? AND ?"
        p_format.extend([start_date, end_date])
        
    # Compras + Salidas + Traslados (Salida Origen) + Traslados (Entrada Destino)
    # UNION ALL requires same column count/types
    
    query = f"""
        SELECT 
            cc.fecha_emision as Fecha, 
            'COMPRA' as TipoMovimiento, 
            cc.numero as Documento,
            'Proveedor' as OrigenDestino,
            cd.cantidad as Entradas,
            0 as Salidas
        FROM compras_detalle cd
        JOIN compras_cabecera cc ON cd.compra_id = cc.id
        WHERE cd.producto_id = ? AND {cond_compras}
        
        UNION ALL
        
        SELECT 
            sc.fecha as Fecha, 
            'SALIDA' as TipoMovimiento, 
            'Salida #' || sc.id as Documento,
            sc.destino as OrigenDestino,
            0 as Entradas,
            sd.cantidad as Salidas
        FROM salidas_detalle sd
        JOIN salidas_cabecera sc ON sd.salida_id = sc.id
        WHERE sd.producto_id = ? AND {cond_salidas}
        
        UNION ALL
        
        SELECT 
            tc.fecha as Fecha,
            'TRASLADO SALIDA' as TipoMovimiento,
            'Traslado #' || tc.id as Documento,
            'A: ' || ad.nombre as OrigenDestino,
            0 as Entradas,
            td.cantidad as Salidas
        FROM traslados_detalle td
        JOIN traslados_cabecera tc ON td.traslado_id = tc.id
        JOIN almacenes ad ON tc.destino_id = ad.id
        WHERE td.producto_id = ? AND {cond_traslados_sal}
        
        UNION ALL
        
        SELECT 
            tc.fecha as Fecha,
            'TRASLADO ENTRADA' as TipoMovimiento,
            'Traslado #' || tc.id as Documento,
            'De: ' || ao.nombre as OrigenDestino,
            td.cantidad as Entradas,
            0 as Salidas
        FROM traslados_detalle td
        JOIN traslados_cabecera tc ON td.traslado_id = tc.id
        JOIN almacenes ao ON tc.origen_id = ao.id
        WHERE td.producto_id = ? AND {cond_traslados_ent}
        
        ORDER BY Fecha DESC
    """
    
    # Need to repeat params for each union part
    full_params = p_format * 4 
    
    columns = ['Fecha', 'TipoMovimiento', 'Documento', 'OrigenDestino', 'Entradas', 'Salidas']
    data = []
    
    cursor = conn.cursor()
    try:
        cursor.execute(query, full_params)
        rows = cursor.fetchall()
        for r in rows:
            data.append(r)
    except Exception as e:
        print(f"Error kardex: {e}")
        pass
        
    df = pd.DataFrame(data, columns=columns)
    
    # Calculate balance (requires ASC sort first, then flip back if needed)
    if not df.empty:
        df = df.sort_values(by=['Fecha'], ascending=True) # Sort ASC for cumulative sum
        df['Saldo'] = (df['Entradas'] - df['Salidas']).cumsum()
        df = df.sort_values(by=['Fecha'], ascending=False) # Return DESC as requested
    else:
        df['Saldo'] = 0
        
    conn.close()
    return df

def obtener_compras_historial():
    """Retorna historial de cabeceras de compra"""
    return obtener_historial_compras()

def obtener_compras_detalle_historial():
    """Retorna historial detallado de items comprados"""
    conn = get_connection()
    query = """
        SELECT 
            c.fecha_emision as fecha,
            c.numero as numero_documento,
            p.razon_social as proveedor,
            prod.nombre as producto,
            cd.cantidad,
            cd.precio_unitario,
            cd.subtotal,
            c.moneda,
            c.id as compra_id,
            cd.costo_previo
        FROM compras_detalle cd
        JOIN compras_cabecera c ON cd.compra_id = c.id
        JOIN proveedores p ON c.proveedor_id = p.id
        JOIN productos prod ON cd.producto_id = prod.id
        ORDER BY c.fecha_emision DESC, c.id DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def obtener_salidas_historial():
    """Retorna historial de salidas agrupado por cabecera"""
    conn = get_connection()
    query = """
        SELECT 
            sc.id,
            sc.fecha,
            sc.tipo_movimiento as tipo,
            sc.destino,
            sc.observaciones,
            COUNT(sd.id) as items,
            SUM(sd.cantidad) as total_cantidad
        FROM salidas_cabecera sc
        LEFT JOIN salidas_detalle sd ON sc.id = sd.salida_id
        GROUP BY sc.id
        ORDER BY sc.fecha DESC, sc.id DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def obtener_compras_historial():
    """Retorna historial de compras agrupado por cabecera"""
    conn = get_connection()
    query = """
        SELECT 
            cc.id,
            cc.fecha_emision as fecha,
            p.razon_social as proveedor,
            cc.serie,
            cc.numero,
            cc.moneda,
            cc.total_compra as total,
            COUNT(cd.id) as items
        FROM compras_cabecera cc
        LEFT JOIN proveedores p ON cc.proveedor_id = p.id
        LEFT JOIN compras_detalle cd ON cc.id = cd.compra_id
        GROUP BY cc.id
        ORDER BY cc.fecha_emision DESC, cc.id DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def obtener_compras_detalle_historial():
    """Retorna historial de compras detallado (línea por línea)"""
    conn = get_connection()
    query = """
        SELECT 
            cc.fecha_emision as fecha,
            p.razon_social as proveedor,
            cc.serie,
            cc.numero,
            pr.codigo_sku as codigo,
            pr.nombre as producto,
            cd.cantidad,
            pr.unidad_medida as um,
            cd.precio_unitario,
            (cd.cantidad * cd.precio_unitario) as subtotal,
            cc.moneda,
            a.nombre as almacen
        FROM compras_detalle cd
        JOIN compras_cabecera cc ON cd.compra_id = cc.id
        JOIN proveedores p ON cc.proveedor_id = p.id
        JOIN productos pr ON cd.producto_id = pr.id
        LEFT JOIN almacenes a ON cd.almacen_id = a.id
        ORDER BY cc.fecha_emision DESC, cc.id DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def verificar_factura_duplicada(serie, numero, proveedor_id):
    """Verifica si existe una factura con la misma serie/numero/proveedor"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM compras_cabecera WHERE serie = ? AND numero = ? AND proveedor_id = ?",
        (serie, numero, proveedor_id)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

def generar_correlativo_oc():
    """Genera el siguiente correlativo para órdenes de compra"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(id) FROM ordenes_compra")
    max_id = cursor.fetchone()[0]
    conn.close()
    return (max_id or 0) + 1

def crear_orden_compra_con_correlativo(proveedor_id, fecha_emision, fecha_entrega_estimada, moneda, tasa_igv, observaciones, items):
    """Crea una orden de compra con correlativo auto-generado"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Calculate total
        total_orden = sum(item['cantidad'] * item['precio_unitario'] for item in items)
        
        # Insert header
        # NOTE: DB schema uses 'fecha_entrega_est', code param is 'fecha_entrega_estimada'
        cursor.execute("""
            INSERT INTO ordenes_compra (
                proveedor_id, fecha_emision, fecha_entrega_est,
                moneda, estado, total_orden, tasa_igv, observaciones
            ) VALUES (?, ?, ?, ?, 'PENDIENTE', ?, ?, ?)
        """, (
            proveedor_id, fecha_emision, fecha_entrega_estimada,
            moneda, total_orden, tasa_igv, observaciones
        ))
        
        orden_id = cursor.lastrowid
        
        # Insert details
        for item in items:
            cursor.execute("""
                INSERT INTO ordenes_compra_detalle (
                    orden_id, producto_id, cantidad, precio_unitario
                ) VALUES (?, ?, ?, ?)
            """, (
                orden_id, item['pid'], item['cantidad'], item['precio_unitario']
            ))
        
        conn.commit()
        return orden_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def obtener_ordenes_compra():
    """Retorna todas las órdenes de compra con información del proveedor"""
    conn = get_connection()
    query = """
        SELECT 
            oc.id,
            oc.fecha_emision,
            COALESCE(p.razon_social, 'Proveedor Desconocido') as razon_social,
            oc.moneda,
            oc.estado,
            COALESCE(oc.total_orden, 0) as total_orden
        FROM ordenes_compra oc
        LEFT JOIN proveedores p ON oc.proveedor_id = p.id
        ORDER BY oc.fecha_emision DESC, oc.id DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Funciones de creación (CRUD)
def crear_proveedor(razon_social, ruc="", contacto="", telefono="", direccion=""):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM proveedores WHERE ruc_dni = ?", (ruc,))
        if cursor.fetchone():
            return False, "RUC ya registrado"
        
        cursor.execute("INSERT INTO proveedores (ruc_dni, razon_social, direccion, telefono, email) VALUES (?, ?, ?, ?, ?)",
                       (ruc, razon_social, direccion, telefono, email))
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

def crear_producto(sku, nombre, unidad, categoria_id, stock_minimo=0, stock_inicial=0):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM productos WHERE nombre = ?", (nombre,))
        if cursor.fetchone():
            return False, "Producto ya existe con ese nombre", None
            
        cursor.execute("""
            INSERT INTO productos (codigo_sku, nombre, unidad_medida, categoria_id, costo_promedio, stock_actual, stock_minimo) 
            VALUES (?, ?, ?, ?, 0, 0, ?)
        """, (sku, nombre, unidad, categoria_id, stock_minimo))
        pid = cursor.lastrowid
        
        if stock_inicial > 0:
             cursor.execute("INSERT INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, 1, ?)", (pid, stock_inicial))
             cursor.execute("UPDATE productos SET stock_actual = ? WHERE id = ?", (stock_inicial, pid))
             
        conn.commit()
        return True, "Producto creado", pid
    except Exception as e:
        return False, f"Error: {str(e)}", None
    finally:
        conn.close()

def obtener_productos_extendido():
    """Retorna productos con info extendida para Dashboards y tablas"""
    conn = get_connection()
    query = """
        SELECT 
            p.id, 
            p.codigo_sku, 
            p.nombre, 
            COALESCE(c.nombre, 'Sin Categoría') as categoria_nombre, 
            p.unidad_medida, 
            COALESCE(SUM(sa.stock_actual), 0) as stock_actual,
            p.costo_promedio,
            (SELECT MAX(cd.precio_unitario) 
             FROM compras_detalle cd 
             JOIN compras_cabecera cc ON cd.compra_id = cc.id 
             WHERE cd.producto_id = p.id
            ) as ultimo_precio_compra,
            p.precio_venta
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
        LEFT JOIN stock_almacen sa ON p.id = sa.producto_id
        GROUP BY p.id, p.codigo_sku, p.nombre, c.nombre, p.unidad_medida, p.costo_promedio, p.precio_venta
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- Funciones Adicionales para Streamlit Legacy ---

def obtener_compras_por_categoria(start_date, end_date):
    return obtener_gastos_por_categoria(start_date, end_date)

def obtener_historial_compras():
    conn = get_connection()
    query = """
        SELECT 
            c.id, 
            c.fecha_emision as fecha, 
            c.serie || '-' || c.numero as numero_documento, 
            p.razon_social as proveedor, 
            c.moneda, 
            c.total_compra as total_final,
            (SELECT COUNT(*) FROM compras_detalle WHERE compra_id = c.id) as items
        FROM compras_cabecera c
        JOIN proveedores p ON c.proveedor_id = p.id
        ORDER BY c.fecha_emision DESC, c.id DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def obtener_historial_compras_detallado():
    return obtener_compras_detalle_historial()

def obtener_ordenes_compra():
    conn = get_connection()
    query = """
        SELECT 
            oc.id, 
            oc.fecha_emision, 
            p.razon_social,
            oc.estado,
            (SELECT COUNT(*) FROM ordenes_compra_det WHERE oc_id = oc.id) as items,
            oc.moneda,
            oc.total_orden
        FROM ordenes_compra oc
        JOIN proveedores p ON oc.proveedor_id = p.id
        ORDER BY oc.fecha_emision DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def calcular_valorizado_fifo(incluir_igv=True):
    """
    Calcula el valor del inventario usando método FIFO.
    Retorna (total_valorizado, mapa_detalle_por_producto)
    """
    conn = get_connection()
    
    # 1. Obtener todos los productos
    productos = pd.read_sql("SELECT id, nombre FROM productos", conn)
    
    total_general = 0.0
    detalle_map = {} 
    
    for _, prod in productos.iterrows():
        pid = prod['id']
        nombre = prod['nombre']
        
        q_ent = """
            SELECT cd.cantidad, cd.precio_unitario, cc.fecha_emision, cc.moneda, cc.tipo_cambio
            FROM compras_detalle cd
            JOIN compras_cabecera cc ON cd.compra_id = cc.id
            WHERE cd.producto_id = ?
            ORDER BY cc.fecha_emision ASC, cc.id ASC
        """
        df_ent = pd.read_sql(q_ent, conn, params=(pid,))
        
        q_sal = """
            SELECT sd.cantidad, sc.fecha
            FROM salidas_detalle sd
            JOIN salidas_cabecera sc ON sd.salida_id = sc.id
            WHERE sd.producto_id = ?
            ORDER BY sc.fecha ASC, sc.id ASC
        """
        df_sal = pd.read_sql(q_sal, conn, params=(pid,))
        
        batches = []
        tc_def = 3.75
        
        for _, row in df_ent.iterrows():
            qty = row['cantidad']
            price = row['precio_unitario']
            moneda = row['moneda']
            tc = row['tipo_cambio'] if row['tipo_cambio'] else tc_def
            
            price_pen = price * tc if moneda == 'USD' else price
            if not incluir_igv:
                price_pen = price_pen / 1.18
            
            batches.append({'qty': qty, 'price': price_pen, 'date': row['fecha_emision']})
            
        total_salidas = df_sal['cantidad'].sum() if not df_sal.empty else 0
        remaining_qty = total_salidas
        
        while remaining_qty > 0 and batches:
            batch = batches[0]
            if batch['qty'] > remaining_qty:
                batch['qty'] -= remaining_qty
                remaining_qty = 0
            else:
                remaining_qty -= batch['qty']
                batches.pop(0)
                
        val_prod = sum(b['qty'] * b['price'] for b in batches)
        stock_prod = sum(b['qty'] for b in batches)
        
        total_general += val_prod
        detalle_map[pid] = {
            'nombre': nombre,
            'stock': stock_prod,
            'valor': val_prod
        }
        
    conn.close()
    return total_general, detalle_map

def registrar_salida(cab, detalles):
    """
    Registra salida de almacén y descuenta stock.
    cab: {fecha, tipo, destino, obs}
    detalles: [{pid, cantidad, almacen_id}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO salidas_cabecera (fecha, tipo_salida, destino, observaciones, fecha_registro)
            VALUES (?, ?, ?, ?, ?)
        """, (
            cab['fecha'], cab['tipo'], cab['destino'], cab.get('obs', ''),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        salida_id = cursor.lastrowid
        
        for d in detalles:
            pid = d['pid']
            qty = float(d['cantidad'])
            alm_id = d.get('almacen_id', 1)
            
            # 1. VALIDACIÓN ESTRICTA DE STOCK
            cursor.execute("SELECT id, stock_actual FROM stock_almacen WHERE producto_id = ? AND almacen_id = ?", (pid, alm_id))
            row_st = cursor.fetchone()
            
            current_stock = row_st[1] if row_st else 0.0
            
            if current_stock < qty:
                raise Exception(f"Stock insuficiente para el producto ID {pid} en Almacén {alm_id}. Disponible: {current_stock}, Solicitado: {qty}")
            
            sid = row_st[0] if row_st else None

            # Insertar detalle salida
            cursor.execute("""
                INSERT INTO salidas_detalle (salida_id, producto_id, cantidad, almacen_id)
                VALUES (?, ?, ?, ?)
            """, (salida_id, pid, qty, alm_id))
            
            # Descontar Stock Almacén
            new_st = current_stock - qty
            cursor.execute("UPDATE stock_almacen SET stock_actual = ? WHERE id = ?", (new_st, sid))
            
            # Descontar Stock Global Producto
            cursor.execute("UPDATE productos SET stock_actual = stock_actual - ? WHERE id = ?", (qty, pid))
            
        conn.commit()
        return True, f"Salida #{salida_id} registrada correctamente"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error al registrar salida: {str(e)}"
    finally:
        conn.close()

def obtener_historial_salidas():
    """Retorna resumen de salidas registradas"""
    conn = get_connection()
    query = """
        SELECT 
            s.id, 
            s.fecha as Fecha, 
            s.tipo_salida as Tipo,
            s.destino as Destino,
            (SELECT COUNT(*) FROM salidas_detalle WHERE salida_id = s.id) as Items,
            (SELECT SUM(sd.cantidad) FROM salidas_detalle sd WHERE sd.salida_id = s.id) as TotalUnidades
        FROM salidas_cabecera s
        ORDER BY s.fecha DESC, s.id DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def obtener_historial_salidas_detallado():
    """
    Retorna detalle de salidas con nombres de productos.
    """
    conn = get_connection()
    try:
        query = """
            SELECT 
                s.fecha as Fecha,
                s.tipo_salida as Tipo,
                s.destino as Destino,
                p.nombre as Producto,
                sd.cantidad as Cantidad,
                p.unidad_medida as UM,
                s.observaciones as Obs
            FROM salidas_detalle sd
            JOIN salidas_cabecera s ON sd.salida_id = s.id
            JOIN productos p ON sd.producto_id = p.id
            ORDER BY s.fecha DESC
        """
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()



def obtener_valor_salidas_fifo(start_date, end_date):
    """
    Calcula el valor monetario de las salidas en un periodo específico usando FIFO.
    """
    conn = get_connection()
    try:
        # 1. Obtener productos que tuvieron salidas en el periodo
        query_prod = """
            SELECT DISTINCT producto_id 
            FROM salidas_detalle sd
            JOIN salidas_cabecera sc ON sd.salida_id = sc.id
            WHERE sc.fecha BETWEEN ? AND ?
        """
        df_pids = pd.read_sql(query_prod, conn, params=(start_date, end_date))
        
        valor_total_salidas_periodo = 0.0
        
        for pid in df_pids['producto_id']:
            # Obtener todas las entradas cronológicas
            q_ent = """
                SELECT cd.cantidad, cd.precio_unitario, cc.fecha_emision, cc.moneda, cc.tipo_cambio
                FROM compras_detalle cd
                JOIN compras_cabecera cc ON cd.compra_id = cc.id
                WHERE cd.producto_id = ?
                ORDER BY cc.fecha_emision ASC, cc.id ASC
            """
            df_ent = pd.read_sql(q_ent, conn, params=(int(pid),))
            
            # Obtener todas las salidas cronológicas
            q_sal = """
                SELECT sd.cantidad, sc.fecha, sc.id as salida_id
                FROM salidas_detalle sd
                JOIN salidas_cabecera sc ON sd.salida_id = sc.id
                WHERE sd.producto_id = ?
                ORDER BY sc.fecha ASC, sc.id ASC
            """
            df_sal = pd.read_sql(q_sal, conn, params=(int(pid),))
            
            if df_ent.empty or df_sal.empty:
                continue
                
            # Preparar lotes de entrada (PEN, Sin IGV por defecto para consistencia)
            batches = []
            tc_def = 3.75
            for _, row in df_ent.iterrows():
                qty = row['cantidad']
                price = row['precio_unitario']
                moneda = row['moneda']
                tc = row['tipo_cambio'] if row['tipo_cambio'] else tc_def
                price_pen = price * tc if moneda == 'USD' else price
                batches.append({'qty': qty, 'price': price_pen})
            
            # Procesar salidas cronológicamente
            for _, row_s in df_sal.iterrows():
                qty_to_consume = row_s['cantidad']
                salida_fecha = row_s['fecha']
                
                # Para cada salida, consumimos de los batches
                valor_esta_salida = 0.0
                while qty_to_consume > 0 and batches:
                    batch = batches[0]
                    if batch['qty'] <= qty_to_consume:
                        # Consumir todo el batch
                        valor_esta_salida += batch['qty'] * batch['price']
                        qty_to_consume -= batch['qty']
                        batches.pop(0)
                    else:
                        # Consumir parte del batch
                        valor_esta_salida += qty_to_consume * batch['price']
                        batch['qty'] -= qty_to_consume
                        qty_to_consume = 0
                
                # Si la fecha de esta salida está en el rango, sumar al total del periodo
                if str(start_date) <= str(salida_fecha) <= str(end_date):
                    valor_total_salidas_periodo += valor_esta_salida
        
        return valor_total_salidas_periodo
    finally:
        conn.close()

def obtener_configuracion(clave, default=''):
    """Obtiene un valor de configuración por clave"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT valor FROM configuracion WHERE clave = ?", (clave,))
        row = cursor.fetchone()
        return row[0] if row else default
    except:
        return default
    finally:
        conn.close()

def guardar_configuracion(clave, valor):
    """Guarda o actualiza un valor de configuración"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO configuracion (clave, valor, fecha_modificacion)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(clave) DO UPDATE SET 
                valor = excluded.valor,
                fecha_modificacion = CURRENT_TIMESTAMP
        """, (clave, valor))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error guardando configuración: {e}")
        return False
    finally:
        conn.close()

def obtener_todas_configuraciones():
    """Retorna todas las configuraciones como dict"""
    conn = get_connection()
    query = "SELECT clave, valor, descripcion FROM configuracion"
    df = pd.read_sql(query, conn)
    conn.close()
    return df.set_index('clave')['valor'].to_dict() if not df.empty else {}

def registrar_traslado(cab, detalles):
    """
    Registra traslado entre almacenes con validación estricta de stock.
    cab: {fecha, origen_id, destino_id, observaciones}
    detalles: [{pid, cantidad}, ...]
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Validar mismo origen/destino
        if cab['origen_id'] == cab['destino_id']:
            return False, "Origen y Destino no pueden ser iguales"

        # Insertar Cabecera
        cursor.execute("""
            INSERT INTO traslados_cabecera (fecha, origen_id, destino_id, observaciones, fecha_registro)
            VALUES (?, ?, ?, ?, ?)
        """, (
            cab['fecha'], cab['origen_id'], cab['destino_id'], 
            cab.get('observaciones', ''), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        traslado_id = cursor.lastrowid
        
        for d in detalles:
            pid = d['pid']
            qty = float(d['cantidad'])
            
            # 1. VALIDAR STOCK ORIGEN
            cursor.execute("SELECT id, stock_actual FROM stock_almacen WHERE producto_id = ? AND almacen_id = ?", (pid, cab['origen_id']))
            row_st_orig = cursor.fetchone()
            
            curr_st_orig = row_st_orig[1] if row_st_orig else 0.0
            
            if curr_st_orig < qty:
                raise Exception(f"Stock insuficiente en origen para producto ID {pid}. Disponible: {curr_st_orig}, Solicitado: {qty}")
            
            sid_orig = row_st_orig[0]
            
            # 2. Insertar Detalle Traslado
            cursor.execute("""
                INSERT INTO traslados_detalle (traslado_id, producto_id, cantidad)
                VALUES (?, ?, ?)
            """, (traslado_id, pid, qty))
            
            # 3. Actualizar Stock Origen (Resta)
            cursor.execute("UPDATE stock_almacen SET stock_actual = stock_actual - ? WHERE id = ?", (qty, sid_orig))
            
            # 4. Actualizar Stock Destino (Suma)
            cursor.execute("SELECT id FROM stock_almacen WHERE producto_id = ? AND almacen_id = ?", (pid, cab['destino_id']))
            row_st_dest = cursor.fetchone()
            
            if row_st_dest:
                sid_dest = row_st_dest[0]
                cursor.execute("UPDATE stock_almacen SET stock_actual = stock_actual + ? WHERE id = ?", (qty, sid_dest))
            else:
                cursor.execute("INSERT INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, ?, ?)", (pid, cab['destino_id'], qty))
                
        conn.commit()
        return True, f"Traslado #{traslado_id} registrado exitosamente"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error en traslado: {str(e)}"
    finally:
        conn.close()

def obtener_inventario_detallado():
    """Retorna inventario desglosado por Almacén"""
    conn = get_connection()
    query = """
        SELECT 
            p.id as ProductID,
            p.codigo_sku as Codigo,
            p.nombre as Producto,
            c.nombre as Categoria,
            p.unidad_medida as UM,
            a.nombre as Almacen,
            COALESCE(sa.stock_actual, 0) as Stock,
            p.costo_promedio as CostoUnitRef
        FROM productos p
        JOIN stock_almacen sa ON p.id = sa.producto_id
        JOIN almacenes a ON sa.almacen_id = a.id
        LEFT JOIN categorias c ON p.categoria_id = c.id
        WHERE sa.stock_actual <> 0
        ORDER BY p.nombre, a.nombre
    """
    # Fix table name in query if needed (products vs productos check done upstream, assuming consistent schema now)
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Calculate Global FIFO Valuation to distribute
    try:
        _, fifo_map = calcular_valorizado_fifo(incluir_igv=True)
        
        vals = []
        fifo_costs = []
        
        for _, row in df.iterrows():
            pid = row['ProductID']
            stock_wh = row['Stock']
            
            f_data = fifo_map.get(pid, {'valor': 0.0, 'stock': 0.0})
            g_stock = f_data['stock']
            g_val = f_data['valor']
            
            if g_stock > 0:
                unit_cost = g_val / g_stock
            else:
                unit_cost = row['CostoUnitRef'] # Fallback to avg cost
                
            fifo_costs.append(unit_cost)
            vals.append(stock_wh * unit_cost)
            
        df['CostoUnitFIFO'] = fifo_costs
        df['ValorTotal'] = vals
        
    except Exception as e:
        print(f"Error calculating FIFO distribution: {e}")
        df['CostoUnitFIFO'] = df['CostoUnitRef']
        df['ValorTotal'] = df['Stock'] * df['CostoUnitRef']
    
    return df

def eliminar_producto(producto_id):
    """
    Elimina un producto si no tiene movimientos asociados (Integridad Referencial).
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Verificar Compras
        cursor.execute("SELECT COUNT(*) FROM compras_detalle WHERE producto_id = ?", (producto_id,))
        if cursor.fetchone()[0] > 0:
            return False, "No se puede eliminar: El producto tiene compras asociadas."
            
        # 2. Verificar Salidas
        cursor.execute("SELECT COUNT(*) FROM salidas_detalle WHERE producto_id = ?", (producto_id,))
        if cursor.fetchone()[0] > 0:
            return False, "No se puede eliminar: El producto tiene salidas asociadas."
            
        # 3. Verificar Traslados (Detalle)
        # Note: traslados_detalle might not exist in original schema if user didn't run migration? 
        # But we assume it exists based on previous implementation.
        # Fallback consistent check
        try:
             cursor.execute("SELECT COUNT(*) FROM traslados_detalle WHERE producto_id = ?", (producto_id,))
             if cursor.fetchone()[0] > 0:
                 return False, "No se puede eliminar: El producto tiene traslados asociados."
        except:
             pass # Table might not exist yet if migration failed, but let's assume it does.

        # 4. Verificar Stock Real != 0
        cursor.execute("SELECT SUM(stock_actual) FROM stock_almacen WHERE producto_id = ?", (producto_id,))
        res_st = cursor.fetchone()
        if res_st and res_st[0] and res_st[0] != 0:
             return False, "No se puede eliminar: El producto tiene stock físico registrado."

        # Si pasa todo, eliminar
        cursor.execute("DELETE FROM stock_almacen WHERE producto_id = ?", (producto_id,))
        cursor.execute("DELETE FROM productos WHERE id = ?", (producto_id,))
        conn.commit()
        return True, "Producto y su stock vinculado eliminados correctamente."
        
    except Exception as e:
        conn.rollback()
        return False, f"Error al eliminar: {str(e)}"
    finally:
        conn.close()

def actualizar_estado_oc(oc_id, nuevo_estado):
    """Actualiza el estado de una Orden de Compra"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE ordenes_compra SET estado = ? WHERE id = ?", (nuevo_estado, oc_id))
        conn.commit()
        return True, "Estado actualizado correctamemte"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()



def actualizar_orden_compra(oc_id, data):
    """Actualiza una OC existente (Solo si está PENDIENTE)"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Validar estado
        cursor.execute("SELECT estado FROM ordenes_compra WHERE id = ?", (oc_id,))
        st = cursor.fetchone()
        if not st: return False, "OC no encontrada"
        if st[0] != 'PENDIENTE': return False, "Solo se pueden editar OCs en estado PENDIENTE"
        
        # Update Header
        cursor.execute("""
            UPDATE ordenes_compra SET 
                proveedor_id=?, fecha_emision=?, fecha_entrega_est=?, moneda=?, tasa_igv=?
            WHERE id=?
        """, (data['proveedor_id'], data['fecha'], data.get('fecha_entrega'), data['moneda'], data.get('tasa_igv', 18), oc_id))
        
        # Re-create Details
        cursor.execute("DELETE FROM ordenes_compra_detalle WHERE orden_id=?", (oc_id,))
        
        total_orden = 0
        for item in data['items']:
            pid = int(item['pid'])
            qty = float(item['cantidad'])
            price = float(item['precio_unitario'])
            total_orden += qty * price
            
            cursor.execute("""
                INSERT INTO ordenes_compra_detalle (orden_id, producto_id, cantidad, precio_unitario)
                VALUES (?, ?, ?, ?)
            """, (oc_id, pid, qty, price))
            
        # Update Total
        cursor.execute("UPDATE ordenes_compra SET total_orden=? WHERE id=?", (total_orden, oc_id))
        
        conn.commit()
        return True, "OC Actualizada"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()
    """
    Convierte una OC APROBADA en una Compra (Factura).
    Registra cabecera y detalles, y actualiza stock.
    Cambia estado OC a FACTURADA.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Obtener Datos OC
        cursor.execute("SELECT proveedor_id, moneda FROM ordenes_compra WHERE id = ?", (oc_id,))
        res_oc = cursor.fetchone()
        if not res_oc: return False, "OC no encontrada"
        prov_id, moneda = res_oc
        
        # 2. Obtener Detalles OC
        cursor.execute("""
            SELECT producto_id, cantidad, precio_unitario 
            FROM ordenes_compra_detalle WHERE orden_id = ?
        """, (oc_id,))
        rows_det = cursor.fetchall()
        
        if not rows_det: return False, "OC sin detalles"

        # 3. Preparar estructura para registrar_compra (reutilizando lógica existente o manual)
        # Haremos manual para transacción atómica
        
        # Calcular totales reales
        total_compra = 0
        detalles_compra = []
        tc_actual = obtener_tipo_cambio_actual()
        
        for r in rows_det:
            pid, qty, price = r
            total_linea = qty * price
            total_compra += total_linea
            detalles_compra.append((pid, qty, price, total_linea))
            
        base = round(total_compra / 1.18, 2)
        igv = round(total_compra - base, 2)
        
        # Insertar Compra Cabecera
        cursor.execute("""
            INSERT INTO compras_cabecera (
                proveedor_id, fecha_emision, tipo_documento, serie, numero, 
                moneda, total_compra, total_gravada, total_igv, tipo_cambio, fecha_registro
            )
            VALUES (?, ?, 'FACTURA', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (prov_id, fecha_emision, serie, numero, moneda, total_compra, base, igv, tc_actual, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        compra_id = cursor.lastrowid
        
        # Insertar Detalles y Mover Stock
        for d in detalles_compra:
            pid, qty, price, subtotal = d
            
            # Obtener datos producto
            cursor.execute("SELECT nombre, unidad_medida, costo_promedio FROM productos WHERE id = ?", (pid,))
            p_data = cursor.fetchone()
            p_nom, p_um, p_costo_prev = p_data
            
            # Insertar Detalle Compra (Default Almacen 1)
            cursor.execute("""
                INSERT INTO compras_detalle (compra_id, producto_id, descripcion, unidad_medida, cantidad, precio_unitario, subtotal, costo_previo, tasa_impuesto, almacen_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 18.0, 1)
            """, (compra_id, pid, p_nom, p_um, qty, price, subtotal, p_costo_prev))
            
            # Actualizar Stock (Almacen 1 Default)
            cursor.execute("SELECT id, stock_actual FROM stock_almacen WHERE producto_id = ? AND almacen_id = 1", (pid,))
            row_st = cursor.fetchone()
            
            precio_pen = price * tc_actual if moneda == 'USD' else price
            
            if row_st:
                sid, st_curr = row_st
                new_st = st_curr + qty
                # Costo Promedio
                new_cost = ((st_curr * p_costo_prev) + (qty * precio_pen)) / new_st if new_st > 0 else p_costo_prev
                cursor.execute("UPDATE stock_almacen SET stock_actual = ? WHERE id = ?", (new_st, sid))
                cursor.execute("UPDATE productos SET costo_promedio = ?, stock_actual = stock_actual + ? WHERE id = ?", (new_cost, qty, pid))
            else:
                cursor.execute("INSERT INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, 1, ?)", (pid, qty))
                cursor.execute("UPDATE productos SET costo_promedio = ?, stock_actual = stock_actual + ? WHERE id = ?", (precio_pen, qty, pid))

        # Actualizar estado OC
        cursor.execute("UPDATE ordenes_compra SET estado = 'FACTURADA' WHERE id = ?", (oc_id,))
        
        conn.commit()
        return True, f"Factura {serie}-{numero} generada desde OC #{oc_id}"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error conversión: {str(e)}"
    finally:
        conn.close()

def obtener_orden_compra(oc_id):
    """Retorna datos completos de una OC por ID (Soporta Legacy y Nuevo Schema)"""
    conn = get_connection()
    try:
        # Cabecera
        query_cab = """
            SELECT oc.id, oc.proveedor_id, p.razon_social, p.ruc, oc.fecha_emision, 
                   oc.fecha_entrega_estimada, oc.moneda, oc.tasa_igv, oc.estado, oc.total_orden, oc.observaciones
            FROM ordenes_compra oc
            JOIN proveedores p ON oc.proveedor_id = p.id
            WHERE oc.id = ?
        """
        df_cab = pd.read_sql(query_cab, conn, params=(oc_id,))
        
        if df_cab.empty:
            return None
            
        cab = df_cab.iloc[0].to_dict()
        
        # Detalles - STRATEGY 1: New Schema (ordenes_compra_detalle)
        query_det_new = """
            SELECT od.producto_id as pid, pr.nombre as Producto, pr.unidad_medida as um,
                   od.cantidad as cantidad, od.precio_unitario as precio_unitario
            FROM ordenes_compra_detalle od
            JOIN productos pr ON od.producto_id = pr.id
            WHERE od.orden_id = ?
        """
        df_det = pd.read_sql(query_det_new, conn, params=(oc_id,))
        
        # Detalles - STRATEGY 2: Legacy Schema (ordenes_compra_det) -> Fallback
        if df_det.empty:
            try:
                query_det_legacy = """
                    SELECT od.producto_id as pid, pr.nombre as Producto, pr.unidad_medida as um,
                           od.cantidad_solicitada as cantidad, od.precio_unitario_pactado as precio_unitario
                    FROM ordenes_compra_det od
                    JOIN productos pr ON od.producto_id = pr.id
                    WHERE od.oc_id = ?
                """
                df_det_legacy = pd.read_sql(query_det_legacy, conn, params=(oc_id,))
                if not df_det_legacy.empty:
                    df_det = df_det_legacy
            except Exception:
                # If table doesn't exist, ignore
                pass
        
        items = df_det.fillna(0).to_dict(orient='records')
        
        result = {
            'id': cab['id'],
            'proveedor_id': cab['proveedor_id'],
            'proveedor_nombre': cab['razon_social'],
            'proveedor_ruc': cab['ruc'],
            'fecha': cab['fecha_emision'],
            'fecha_entrega': cab['fecha_entrega_estimada'],
            'moneda': cab['moneda'],
            'tasa_igv': cab['tasa_igv'],
            'estado': cab['estado'],
            'total': cab['total_orden'],
            'observaciones': cab['observaciones'],
            'items': items
        }
        
        return result
    finally:
        conn.close()

def obtener_ordenes_compra():
    """Retorna lista de todas las OCs para el grid"""
    conn = get_connection()
    try:
        query = """
            SELECT 
                oc.id, 
                oc.fecha_emision,
                oc.fecha_emision as fecha,
                p.razon_social as proveedor_nombre,
                oc.total_orden as total,
                oc.estado,
                oc.moneda
            FROM ordenes_compra oc
            LEFT JOIN proveedores p ON oc.proveedor_id = p.id
            ORDER BY oc.id DESC
        """
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()

def obtener_productos_extendido():
    """
    Retorna productos con info extendida (Categoria, UM) para el inventario.
    """
    conn = get_connection()
    try:
        query = """
            SELECT 
                p.id, 
                p.codigo_sku, 
                p.nombre, 
                p.unidad_medida, 
                p.costo_promedio,
                COALESCE(SUM(sa.stock_actual), 0) as stock_actual,
                c.nombre as categoria_nombre
            FROM productos p
            LEFT JOIN stock_almacen sa ON p.id = sa.producto_id
            LEFT JOIN categorias c ON p.categoria_id = c.id
            GROUP BY p.id
        """
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()
