import pandas as pd
import sqlite3
from datetime import datetime
from src.database.db import get_connection

# --- CRUD BASICOS ---

def obtener_productos():
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT id, nombre, codigo_sku, categoria_id, unidad_medida, stock_actual, stock_minimo, ROUND(costo_promedio, 2) as costo_promedio, ROUND(precio_venta, 2) as precio_venta FROM productos", conn)
        return df
    finally:
        conn.close()

def obtener_productos_extendido():
    """Retorna productos con nombre de categoría y stock"""
    conn = get_connection()
    query = """
        SELECT p.id, p.nombre, p.codigo_sku, c.nombre as categoria_nombre, 
               p.unidad_medida, p.stock_actual, p.stock_minimo, p.costo_promedio, p.precio_venta
        FROM productos p
        LEFT JOIN categories c ON p.categoria_id = c.id
        -- Note: Table name might be 'categorias' in DB, check schema. 
        -- Based on backend.py line 235: 'JOIN categorias cat'
        -- Let's fix table name to 'categorias'
    """
    # Fixing query based on inspection of backend.py
    query = """
        SELECT p.id, p.nombre, p.codigo_sku, c.nombre as categoria_nombre, 
               p.unidad_medida, p.stock_actual, p.stock_minimo, p.costo_promedio, p.precio_venta
        FROM productos p
        LEFT JOIN categorias c ON p.categoria_id = c.id
    """
    try:
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        print(f"Error obtener_productos_extendido: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def crear_producto(data):
    conn = get_connection()
    try:
        # Check SKU
        if data.get('codigo_sku'):
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM productos WHERE codigo_sku = ?", (data['codigo_sku'],))
            if cursor.fetchone():
                return False, "SKU ya existe"
        
        conn.execute("""
            INSERT INTO productos (nombre, codigo_sku, categoria_id, precio_venta, costo_promedio, stock_minimo, unidad_medida, stock_actual)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            data['nombre'], 
            data.get('codigo_sku'), 
            data.get('categoria_id'), 
            data.get('precio_venta', 0), 
            data.get('costo_promedio', 0), 
            data.get('stock_minimo', 5), 
            data.get('unidad_medida', 'UN')
        ))
        conn.commit()
        return True, "Producto creado"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def obtener_almacenes():
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT id, nombre, ubicacion FROM almacenes", conn)
        return df
    finally:
        conn.close()

def crear_almacen(nombre, ubicacion=""):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO almacenes (nombre, ubicacion) VALUES (?, ?)", (nombre, ubicacion))
        conn.commit()
        return True, "Almacén creado"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def obtener_categorias():
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT id, nombre, descripcion FROM categorias", conn)
        return df
    finally:
        conn.close()

def crear_categoria(nombre, descripcion=""):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion))
        conn.commit()
        return True, "Categoría creada"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- INVENTARIO AVANZADO ---

def obtener_inventario_detallado():
    """Retorna stock por almacén con valorización"""
    conn = get_connection()
    query = """
        SELECT 
            p.nombre as Producto, 
            p.codigo_sku as Codigo, 
            a.nombre as Almacen, 
            sa.stock_actual as Stock,
            p.costo_promedio as CostoUnitFIFO,
            (sa.stock_actual * p.costo_promedio) as ValorTotal
        FROM stock_almacen sa
        JOIN productos p ON sa.producto_id = p.id
        JOIN almacenes a ON sa.almacen_id = a.id
        WHERE sa.stock_actual > 0
        ORDER BY p.nombre, a.nombre
    """
    try:
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()

def calcular_valorizado_fifo(incluir_igv=True):
    """
    Calcula valor del inventario usando FIFO real.
    Retorna (TotalValor, Dict{product_id: {valor, stock_restante}})
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    
    # 1. Obtener Stock Actual y Costo Promedio (Global)
    df_stock = pd.read_sql("SELECT id, stock_actual, costo_promedio FROM productos WHERE stock_actual > 0", conn)
    
    # 2. Obtener Compras (Entradas) ordenadas por fecha DESC
    query = """
        SELECT cd.producto_id, cd.cantidad, cd.precio_unitario, cd.subtotal, cc.fecha_emision, cc.moneda, cc.tipo_cambio
        FROM compras_detalle cd
        JOIN compras_cabecera cc ON cd.compra_id = cc.id
        ORDER BY cc.fecha_emision DESC, cc.id DESC
    """
    cursor = conn.cursor()
    cursor.execute(query)
    compras = cursor.fetchall()
    
    conn.close()
    
    map_valor = {}
    total_valor = 0.0
    
    # Group inputs by product
    entradas_por_prod = {}
    for c in compras:
        pid = c['producto_id']
        if pid not in entradas_por_prod: entradas_por_prod[pid] = []
        
        # Normalize cost to PEN
        costo_unit = c['precio_unitario']
        if c['moneda'] == 'USD':
            tc = c['tipo_cambio'] if c['tipo_cambio'] else 3.75
            costo_unit *= tc
            
        entradas_por_prod[pid].append({
            'qty': c['cantidad'],
            'cost': costo_unit
        })
        
    # Calculate
    for _, row in df_stock.iterrows():
        pid = row['id']
        stock_rem = row['stock_actual']
        valor_prod = 0.0
        
        entradas = entradas_por_prod.get(pid, [])
        
        # Iterate recent purchases to cover stock
        for ent in entradas:
            if stock_rem <= 0: break
            
            tomar = min(stock_rem, ent['qty'])
            valor_prod += tomar * ent['cost']
            stock_rem -= tomar
            
        # Fallback to Average Cost for older stock or initial inventory
        if stock_rem > 0:
            costo_prom = row['costo_promedio'] if pd.notna(row['costo_promedio']) else 0.0
            valor_prod += stock_rem * costo_prom
            
        map_valor[pid] = {'valor': valor_prod}
        total_valor += valor_prod
        
    return total_valor, map_valor

def obtener_rotacion_inventario():
    conn = get_connection()
    try:
        # Top 10 High Rotation
        query_top = """
            SELECT p.nombre as Producto, SUM(sd.cantidad) as TotalSalidas, p.stock_actual as StockActual, p.unidad_medida as UM
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
        
        # Low Rotation
        query_bottom = """
            SELECT p.nombre as Producto, COALESCE(SUM(sd.cantidad), 0) as TotalSalidas, p.stock_actual as StockActual, p.unidad_medida as UM
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
        
        return pd.concat([df_top, df_bottom], ignore_index=True)
    except Exception as e:
        print(f"Error rotacion: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def obtener_stock_critico():
    conn = get_connection()
    try:
        query = """
            SELECT p.nombre as Producto, p.stock_actual as Stock, p.unidad_medida as UM, p.stock_minimo as StockMinimo,
                CASE 
                    WHEN p.stock_actual <= 0 THEN 'Sin Stock'
                    WHEN p.stock_minimo > 0 AND p.stock_actual <= p.stock_minimo * 0.5 THEN 'Crítico'
                    WHEN p.stock_minimo > 0 AND p.stock_actual <= p.stock_minimo THEN 'Bajo'
                    ELSE 'Normal'
                END as Estado
            FROM productos p
            WHERE p.stock_minimo > 0 AND Estado IN ('Sin Stock', 'Crítico', 'Bajo')
            ORDER BY CASE Estado WHEN 'Sin Stock' THEN 1 WHEN 'Crítico' THEN 2 WHEN 'Bajo' THEN 3 ELSE 4 END, Stock ASC
            LIMIT 15
        """
        return pd.read_sql(query, conn)
    except Exception as e:
        print(f"Error stock critico: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def registrar_salida(cabecera, detalles):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO salidas_cabecera (fecha, tipo, destino, observaciones) VALUES (?, ?, ?, ?)",
                       (cabecera['fecha'], cabecera['tipo'], cabecera.get('destino'), cabecera.get('obs')))
        salida_id = cursor.lastrowid
        
        for d in detalles:
            # Validar stock en almacen especifico
            almacen_id = d.get('almacen_id', 1)
            cursor.execute("SELECT stock_actual FROM stock_almacen WHERE producto_id = ? AND almacen_id = ?", (d['pid'], almacen_id))
            row = cursor.fetchone()
            curr_stock = row[0] if row else 0
            
            if curr_stock < float(d['cantidad']):
                raise Exception(f"Stock insuficiente para producto ID {d['pid']} en almacén {almacen_id}")
            
            # Registrar detalle
            cursor.execute("INSERT INTO salidas_detalle (salida_id, producto_id, cantidad, almacen_id) VALUES (?, ?, ?, ?)",
                           (salida_id, d['pid'], d['cantidad'], almacen_id))
            
            # Actualizar stock almacen
            cursor.execute("UPDATE stock_almacen SET stock_actual = stock_actual - ? WHERE producto_id = ? AND almacen_id = ?",
                           (d['cantidad'], d['pid'], almacen_id))
            
            # Actualizar stock global
            cursor.execute("UPDATE productos SET stock_actual = stock_actual - ? WHERE id = ?",
                           (d['cantidad'], d['pid']))
                           
        conn.commit()
        return True, "Salida registrada"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def registrar_traslado(cabecera, detalles):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Create transfer record if table exists (traslados), assuming yes based on backend.py usage
        # backend.py didn't show 'registrar_traslado' body fully, but showed usage in main.py
        # Creating simple implementation
        
        # 1. Deduct from Origin
        for d in detalles:
            orig_id = cabecera['origen_id']
            dest_id = cabecera['destino_id']
            pid = d['pid']
            qty = float(d['cantidad'])
            
            # Check Origin Stock
            cursor.execute("SELECT stock_actual FROM stock_almacen WHERE producto_id = ? AND almacen_id = ?", (pid, orig_id))
            row = cursor.fetchone()
            st_orig = row[0] if row else 0
            
            if st_orig < qty:
                raise Exception(f"Stock insuficiente en origen para producto {pid}")
                
            # Update Origin
            cursor.execute("UPDATE stock_almacen SET stock_actual = stock_actual - ? WHERE producto_id = ? AND almacen_id = ?",
                           (qty, pid, orig_id))
            
            # Update Dest
            # Check if exists
            cursor.execute("SELECT id FROM stock_almacen WHERE producto_id = ? AND almacen_id = ?", (pid, dest_id))
            if cursor.fetchone():
                cursor.execute("UPDATE stock_almacen SET stock_actual = stock_actual + ? WHERE producto_id = ? AND almacen_id = ?",
                               (qty, pid, dest_id))
            else:
                cursor.execute("INSERT INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, ?, ?)",
                               (pid, dest_id, qty))
                               
        conn.commit()
        return True, "Traslado exitoso"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

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
        
        ORDER BY Fecha ASC
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
        df['Entradas'] = pd.to_numeric(df['Entradas'], errors='coerce').fillna(0)
        df['Salidas'] = pd.to_numeric(df['Salidas'], errors='coerce').fillna(0)
        df['Saldo'] = (df['Entradas'] - df['Salidas']).cumsum()
        df = df.sort_values(by=['Fecha'], ascending=False)
    else:
        df['Saldo'] = 0
        

    conn.close()
    return df

def obtener_kardex_general(start_date=None, end_date=None):
    """Retorna Kardex consolidado de todos los productos"""
    conn = get_connection()
    
    params = []
    cond_compras = "True"
    cond_salidas = "True"
    
    if start_date and end_date:
        cond_compras = "cc.fecha_emision BETWEEN ? AND ?"
        cond_salidas = "sc.fecha BETWEEN ? AND ?"
        params.extend([start_date, end_date])
        params.extend([start_date, end_date])
        
    query = f"""
        SELECT 
            cc.fecha_emision as Fecha, 
            p.nombre as Producto,
            cat.nombre as Categoria,
            'COMPRA' as TipoMovimiento, 
            cc.numero as Documento,
            cd.cantidad as Entradas,
            0 as Salidas,
            p.unidad_medida as UM
        FROM compras_detalle cd
        JOIN compras_cabecera cc ON cd.compra_id = cc.id
        JOIN productos p ON cd.producto_id = p.id
        LEFT JOIN categorias cat ON p.categoria_id = cat.id
        WHERE {cond_compras}
        
        UNION ALL
        
        SELECT 
            sc.fecha as Fecha, 
            p.nombre as Producto,
            cat.nombre as Categoria,
            'SALIDA' as TipoMovimiento, 
            'Salida #' || sc.id as Documento,
            0 as Entradas,
            sd.cantidad as Salidas,
            p.unidad_medida as UM
        FROM salidas_detalle sd
        JOIN salidas_cabecera sc ON sd.salida_id = sc.id
        JOIN productos p ON sd.producto_id = p.id
        LEFT JOIN categorias cat ON p.categoria_id = cat.id
        WHERE {cond_salidas}
        
        ORDER BY Fecha DESC
    """
    
    try:
        df = pd.read_sql(query, conn, params=params)
        return df
    except Exception as e:
        print(f"Error kardex general: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def carga_masiva_productos(df):
    """
    Carga masiva de productos desde DataFrame.
    Actualiza si existe (por SKU), inserta si no.
    Columns expected: Nombre, CodigoSKU, Categoria, PrecioVenta, CostoPromedio, StockMinimo, UnidadMedida
    """
    conn = get_connection()
    cursor = conn.cursor()
    log_errors = []
    processed = 0
    
    try:
        # Normalize columns
        cols_map = {c.lower().strip(): c for c in df.columns}
        
        # Mapping
        col_sku = cols_map.get('codigosku') or cols_map.get('sku')
        col_nombre = cols_map.get('nombre') or cols_map.get('producto')
        col_cat = cols_map.get('categoria')
        
        if not (col_sku and col_nombre):
             return "Error: Columnas mínimas requeridas: Nombre, CodigoSKU"

        # Cache Categories to avoid repetitive selects
        cursor.execute("SELECT lower(nombre), id FROM categorias")
        cat_map = dict(cursor.fetchall())
        
        for index, row in df.iterrows():
            sku = str(row[col_sku]).strip()
            nombre = str(row[col_nombre]).strip()
            
            # Category Logic
            cat_id = None
            if col_cat and pd.notna(row[col_cat]):
                cat_name = str(row[col_cat]).strip()
                cat_lower = cat_name.lower()
                if cat_lower in cat_map:
                    cat_id = cat_map[cat_lower]
                else:
                    # Create Category on the fly? Or Error?
                    # Let's create it for UX
                    try:
                        cursor.execute("INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)", (cat_name, "Auto-created"))
                        cat_id = cursor.lastrowid
                        cat_map[cat_lower] = cat_id
                    except:
                        pass
            
            # Map other fields
            precio = float(row.get(cols_map.get('precioventa'), 0)) if cols_map.get('precioventa') else 0.0
            costo = float(row.get(cols_map.get('costopromedio'), 0)) if cols_map.get('costopromedio') else 0.0
            min_stock = float(row.get(cols_map.get('stockminimo'), 5)) if cols_map.get('stockminimo') else 5.0
            um = str(row.get(cols_map.get('unidadmedida'), 'UN')).strip() if cols_map.get('unidadmedida') else 'UN'
            
            # Check Exist
            cursor.execute("SELECT id FROM productos WHERE codigo_sku = ?", (sku,))
            exist = cursor.fetchone()
            
            if exist:
                pid = exist[0]
                cursor.execute("""
                    UPDATE productos SET 
                        nombre=?, categoria_id=?, precio_venta=?, stock_minimo=?, unidad_medida=?, costo_promedio=?
                    WHERE id=?
                """, (nombre, cat_id, precio, min_stock, um, costo, pid))
            else:
                cursor.execute("""
                    INSERT INTO productos (nombre, codigo_sku, categoria_id, precio_venta, costo_promedio, stock_minimo, unidad_medida, stock_actual)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                """, (nombre, sku, cat_id, precio, costo, min_stock, um))
            
            processed += 1
            
        conn.commit()
        return f"Procesados {processed} productos."
        
    except Exception as e:
        conn.rollback()
        return f"Error carga masiva: {str(e)}"
    finally:
        conn.close()

def carga_masiva_stock_inicial(df, almacen_id=1):
    """
    Carga masiva de inventario inicial.
    Columns: CodigoSKU, Cantidad, CostoUnitario
    """
    conn = get_connection()
    cursor = conn.cursor()
    log = []
    processed = 0
    
    try:
        cols_map = {c.lower().strip(): c for c in df.columns}
        col_sku = cols_map.get('codigosku') or cols_map.get('sku')
        col_qty = cols_map.get('cantidad') or cols_map.get('stock')
        col_cost = cols_map.get('costounitario') or cols_map.get('costo') # Optional
        
        if not (col_sku and col_qty):
            return "Error: Columnas requeridas: CodigoSKU, Cantidad"
            
        for index, row in df.iterrows():
            sku = str(row[col_sku]).strip()
            try:
                qty = float(row[col_qty])
                cost = float(row[col_cost]) if col_cost and pd.notna(row[col_cost]) else 0.0
            except:
                log.append(f"Fila {index}: Datos numéricos inválidos")
                continue
                
            # Find Product
            cursor.execute("SELECT id, stock_actual, costo_promedio FROM productos WHERE codigo_sku = ?", (sku,))
            prod = cursor.fetchone()
            if not prod:
                log.append(f"SKU {sku} no encontrado")
                continue
                
            pid = prod[0]
            
            # Update Almacen Stock
            cursor.execute("SELECT id, stock_actual FROM stock_almacen WHERE producto_id=? AND almacen_id=?", (pid, almacen_id))
            st_row = cursor.fetchone()
            
            old_st = 0
            if st_row:
                old_st = st_row[1]
                cursor.execute("UPDATE stock_almacen SET stock_actual=? WHERE id=?", (qty, st_row[0]))
            else:
                cursor.execute("INSERT INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, ?, ?)", (pid, almacen_id, qty))
                
            # Update Global Stock (Diff)
            diff = qty - old_st
            cursor.execute("UPDATE productos SET stock_actual = stock_actual + ? WHERE id=?", (diff, pid))
            
            # Update Cost if provided
            if cost > 0:
                cursor.execute("UPDATE productos SET costo_promedio = ? WHERE id=?", (cost, pid))
                
            processed += 1
            
        conn.commit()
        return f"Stock actualizado para {processed} items. {len(log)} errores."
    except Exception as e:
        conn.rollback()
        return f"Error carga stock: {str(e)}"
    finally:
        conn.close()
