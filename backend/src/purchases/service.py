
import pandas as pd
from datetime import datetime
from src.database.db import get_connection
from src.shared.external_api import obtener_tc_sunat
from src.inventory.service import obtener_productos_extendido

# --- PROVIDERS ---

def obtener_proveedores():
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT id, ruc_dni, razon_social, direccion, telefono, email, categoria FROM proveedores", conn)
        return df
    finally:
        conn.close()

def crear_proveedor(data):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Check if RUC exists
        if data.get('ruc'):
            cursor.execute("SELECT id FROM proveedores WHERE ruc_dni = ?", (data['ruc'],))
            if cursor.fetchone():
                return False, "Proveedor con este RUC ya existe"

        cursor.execute("""
            INSERT INTO proveedores (ruc_dni, razon_social, direccion, telefono, email, categoria)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get('ruc'),
            data['razon_social'],
            data.get('direccion'),
            data.get('telefono'),
            data.get('email'),
            data.get('categoria', 'GENERAL')
        ))
        conn.commit()
        return True, "Proveedor creado"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# --- PURCHASES (FACTURAS) ---

def obtener_compras_historial():
    """Retorna historial de cabeceras de compra"""
    conn = get_connection()
    query = """
        SELECT 
            cc.id, 
            cc.fecha_emision as fecha, 
            (cc.serie || '-' || cc.numero) as numero_documento,
            cc.orden_compra_id as oc_id,
            p.razon_social as proveedor, 
            cc.moneda, 
            cc.total_compra as total_final
        FROM compras_cabecera cc
        JOIN proveedores p ON cc.proveedor_id = p.id
        ORDER BY cc.fecha_emision DESC
    """
    try:
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()

def obtener_detalle_compras():
    """Retorna historial detallado (linea por linea)"""
    conn = get_connection()
    query = """
        SELECT 
            cc.fecha_emision as fecha, 
            p.razon_social as proveedor, 
            cc.serie, cc.numero,
            prod.nombre as producto, 
            cd.cantidad, 
            cd.unidad_medida as um, 
            cd.precio_unitario, 
            cd.subtotal, 
            cc.moneda
        FROM compras_detalle cd
        JOIN compras_cabecera cc ON cd.compra_id = cc.id
        JOIN proveedores p ON cc.proveedor_id = p.id
        JOIN productos prod ON cd.producto_id = prod.id
        ORDER BY cc.fecha_emision DESC
    """
    try:
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()

def registrar_compra(cabecera, detalles):
    """
    Registra una compra (factura) completa y actualiza stock/costos.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Calculate totals
        tasa_igv = float(cabecera.get('tasa_igv', 18))
        total_raw = float(cabecera['total'])
        base = round(total_raw / (1 + tasa_igv / 100), 2)
        igv = round(total_raw - base, 2)
        
        # Handle Document Number
        serie = cabecera.get('serie', '')
        numero = cabecera.get('numero', '')
                
        # Obtener TC actual
        tc_actual = obtener_tc_sunat()
                
        cursor.execute("""
            INSERT INTO compras_cabecera (
                proveedor_id, fecha_emision, tipo_documento, serie, numero, 
                moneda, total_compra, total_gravada, total_igv, tipo_cambio, fecha_registro, orden_compra_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cabecera['proveedor_id'], 
            cabecera.get('fecha_emision', cabecera.get('fecha')), 
            cabecera.get('tipo_documento', 'FACTURA'),
            serie,
            numero,
            cabecera['moneda'], 
            total_raw,
            base,
            igv,
            tc_actual,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cabecera.get('orden_compra_id')
        ))
        compra_id = cursor.lastrowid
        
        # Link OC if present
        if cabecera.get('orden_compra_id'):
            oc_id = cabecera['orden_compra_id']
            cursor.execute("UPDATE ordenes_compra SET estado = 'ATENDIDO' WHERE id = ?", (oc_id,))
        
        # Procesar Detalles
        almacen_defecto = cabecera.get('almacen_id')
        if not almacen_defecto:
            return {'success': False, 'error': "Debe seleccionar un almacén de destino"}
            
        # Validar existencia del almacén
        cursor.execute("SELECT id FROM almacenes WHERE id = ?", (almacen_defecto,))
        if not cursor.fetchone():
            return {'success': False, 'error': f"El almacén con ID {almacen_defecto} no existe"}
        
        for d in detalles:
            pid = d.get('producto_id', d.get('pid'))
            qty = float(d['cantidad'])
            precio = float(d['precio_unitario'])
            
            # Unidad de medida (simple logic for now, assuming compatibility)
            # In a full migration we would include unit_converter logic
            
            # Update Product Cost and Global Stock
            cursor.execute("SELECT stock_actual, costo_promedio FROM productos WHERE id = ?", (pid,))
            row_prod = cursor.fetchone()
            stock_ant = row_prod[0] if row_prod else 0
            costo_ant = row_prod[1] if row_prod else 0
            
            # Convert price to PEN if needed
            precio_pen = precio * tc_actual if cabecera['moneda'] == 'USD' else precio
            
            nuevo_stock = stock_ant + qty
            if nuevo_stock > 0:
                nuevo_costo = ((stock_ant * costo_ant) + (qty * precio_pen)) / nuevo_stock
            else:
                nuevo_costo = precio_pen
                
            cursor.execute("UPDATE productos SET stock_actual = ?, costo_promedio = ? WHERE id = ?", 
                           (nuevo_stock, nuevo_costo, pid))
            
            # Insert Detail
            cursor.execute("""
                INSERT INTO compras_detalle (compra_id, producto_id, cantidad, precio_unitario, subtotal, almacen_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (compra_id, pid, qty, precio, qty*precio, almacen_defecto))
            
            # Update Warehouse Stock
            cursor.execute("SELECT id FROM stock_almacen WHERE producto_id = ? AND almacen_id = ?", (pid, almacen_defecto))
            if cursor.fetchone():
                cursor.execute("UPDATE stock_almacen SET stock_actual = stock_actual + ? WHERE producto_id = ? AND almacen_id = ?",
                               (qty, pid, almacen_defecto))
            else:
                cursor.execute("INSERT INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, ?, ?)",
                               (pid, almacen_defecto, qty))
                               
        conn.commit()
        return {'success': True, 'compra_id': compra_id}
        
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

# --- PURCHASE ORDERS (OC) ---

def obtener_ordenes_compra():
    conn = get_connection()
    try:
        query = """
            SELECT 
                oc.id, 
                p.razon_social as proveedor_nombre, 
                oc.fecha_emision as fecha, 
                oc.fecha_entrega_est, 
                oc.moneda, 
                oc.estado, 
                (SELECT COUNT(*) FROM ordenes_compra_det WHERE oc_id = oc.id) as Items,
                COALESCE((SELECT SUM(ROUND(cantidad_solicitada * precio_unitario_pactado, 2)) FROM ordenes_compra_det WHERE oc_id = oc.id), 0) as total
            FROM ordenes_compra oc
            JOIN proveedores p ON oc.proveedor_id = p.id
            ORDER BY oc.id DESC
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def obtener_ordenes_pendientes():
    conn = get_connection()
    try:
        query = """
            SELECT 
                oc.id, 
                p.razon_social as proveedor_nombre, 
                oc.fecha_emision as fecha, 
                oc.moneda, 
                oc.estado,
                p.id as proveedor_id
            FROM ordenes_compra oc
            JOIN proveedores p ON oc.proveedor_id = p.id
            WHERE oc.estado IN ('PENDIENTE', 'PARCIAL', 'APROBADA')
            ORDER BY oc.id DESC
        """
        return pd.read_sql(query, conn)
    finally:
        conn.close()


def obtener_saldo_orden(oid):
    """
    Calcula el saldo pendiente de una OC basándose en las Guías de Remisión registradas.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        
        # 1. Obtener Items de la OC
        cursor.execute("""
            SELECT 
                ocd.producto_id,
                p.nombre,
                p.unidad_medida,
                ocd.cantidad_solicitada
            FROM ordenes_compra_det ocd
            JOIN productos p ON ocd.producto_id = p.id
            WHERE ocd.oc_id = ?
        """, (oid,))
        
        rows = cursor.fetchall()
        items = []
        fully_completed = True
        
        for row in rows:
            pid, nombre, um, solicitado = row
            
            # 2. Calcular lo recibido en Guías asociadas a esta OC
            cursor.execute("""
                SELECT COALESCE(SUM(gd.cantidad_recibida), 0)
                FROM guias_remision_det gd
                JOIN guias_remision g ON gd.guia_id = g.id
                WHERE g.oc_id = ? AND gd.producto_id = ?
            """, (oid, pid))
            
            recibido = cursor.fetchone()[0]
            pendiente = max(0, solicitado - recibido)
            
            if pendiente > 0.001: # Tolerance for floats
                fully_completed = False
                
            items.append({
                "pid": pid,
                "producto": nombre,
                "um": um,
                "cantidad_solicitada": solicitado,
                "cantidad_recibida": recibido,
                "cantidad_pendiente": pendiente
            })
            
        return {
            "oid": oid,
            "fully_completed": fully_completed,
            "items": items
        }
    finally:
        conn.close()

def obtener_orden_compra(oid):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT oc.*, 
                   oc.fecha_emision as fecha,
                   p.razon_social as proveedor_nombre, 
                   p.ruc_dni as proveedor_ruc, 
                   p.direccion as proveedor_direccion,
                   (SELECT COALESCE(SUM(ROUND(cantidad_solicitada * precio_unitario_pactado, 2)), 0) FROM ordenes_compra_det WHERE oc_id = oc.id) as total
            FROM ordenes_compra oc
            JOIN proveedores p ON oc.proveedor_id = p.id
            WHERE oc.id = ?
        """, (oid,))
        row = cursor.fetchone()
        if not row: return None
        
        # Get Items
        # Note: We need column names for row factory to work or manual mapping
        # Let's use simple dict mapping if not using row_factory
        cols = [description[0] for description in cursor.description]
        header = dict(zip(cols, row))
        
        cursor.execute("""
            SELECT 
                ocd.id,
                ocd.oc_id,
                ocd.producto_id,
                p.nombre as Producto, 
                p.codigo_sku,
                p.unidad_medida as um,
                ocd.cantidad_solicitada as cantidad,
                ocd.precio_unitario_pactado as precio_unitario
            FROM ordenes_compra_det ocd
            JOIN productos p ON ocd.producto_id = p.id
            WHERE ocd.oc_id = ?
        """, (oid,))
        items_rows = cursor.fetchall()
        items_cols = [description[0] for description in cursor.description]
        items = [dict(zip(items_cols, r)) for r in items_rows]
        
        return {"header": header, "items": items}
    finally:
        conn.close()

def crear_orden_compra_con_correlativo(proveedor_id, fecha_emision, fecha_entrega_estimada, moneda, tasa_igv, observaciones, items):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO ordenes_compra (proveedor_id, fecha_emision, fecha_entrega_est, estado, moneda, observaciones)
            VALUES (?, ?, ?, 'PENDIENTE', ?, ?)
        """, (proveedor_id, fecha_emision, fecha_entrega_estimada, moneda, observaciones))
        oc_id = cursor.lastrowid
        
        for item in items:
            cursor.execute("""
                INSERT INTO ordenes_compra_det (oc_id, producto_id, cantidad_solicitada, precio_unitario_pactado)
                VALUES (?, ?, ?, ?)
            """, (oc_id, item['pid'], item['cantidad'], item['precio_unitario']))
            
        conn.commit()
        return oc_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def actualizar_estado_oc(oid, status):
    conn = get_connection()
    try:
        conn.execute("UPDATE ordenes_compra SET estado = ? WHERE id = ?", (status, oid))
        conn.commit()
        return True, "Estado actualizado"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def carga_masiva_proveedores(df):
    """
    Carga masiva de proveedores.
    Columns: RUC, RazonSocial, Direccion, Telefono, Email, Categoria
    """
    conn = get_connection()
    cursor = conn.cursor()
    log = []
    processed = 0
    try:
        cols_map = {c.lower().strip(): c for c in df.columns}
        col_ruc = cols_map.get('ruc')
        col_name = cols_map.get('razonsocial') or cols_map.get('proveedor') or cols_map.get('razon_social')
        
        if not (col_ruc and col_name):
            return "Error: Columnas requeridas: RUC, RazonSocial"
            
        for index, row in df.iterrows():
            ruc = str(row[col_ruc]).strip()
            nombre = str(row[col_name]).strip()
            
            # Upsert Logic
            cursor.execute("SELECT id FROM proveedores WHERE ruc_dni = ?", (ruc,))
            exist = cursor.fetchone()
            
            dir_col = cols_map.get('direccion')
            tel_col = cols_map.get('telefono')
            email_col = cols_map.get('email')
            cat_col = cols_map.get('categoria')

            direccion = str(row[dir_col]).strip() if dir_col and pd.notna(row[dir_col]) else ""
            tel = str(row[tel_col]).strip() if tel_col and pd.notna(row[tel_col]) else ""
            email = str(row[email_col]).strip() if email_col and pd.notna(row[email_col]) else ""
            cat = str(row[cat_col]).strip() if cat_col and pd.notna(row[cat_col]) else "GENERAL"
            
            if exist:
                pid = exist[0]
                cursor.execute("""
                    UPDATE proveedores SET razon_social=?, direccion=?, telefono=?, email=?, categoria=?
                    WHERE id=?
                """, (nombre, direccion, tel, email, cat, pid))
            else:
                cursor.execute("""
                    INSERT INTO proveedores (ruc_dni, razon_social, direccion, telefono, email, categoria)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (ruc, nombre, direccion, tel, email, cat))
            
            processed += 1
            
        conn.commit()
        return f"Procesados {processed} proveedores."
    except Exception as e:
        conn.rollback()
        return f"Error carga proveedores: {str(e)}"
    finally:
        conn.close()

def carga_masiva_compras(df):
    """
    Carga masiva de compras (Cabecera + Detalles flat).
    Columns: Fecha, RUC_Proveedor, TipoDoc, Serie, Numero, Moneda, Total (Cab), ProductoSKU, Cantidad, PrecioUnitario
    Strategy: Group by (RUC, Serie, Numero) to build Invoice.
    """
    conn = None # Initialize variable for safety
    try:
        cols_map = {c.lower().strip(): c for c in df.columns}
        
        # Keys for grouping
        c_ruc = cols_map.get('ruc_proveedor') or cols_map.get('ruc')
        c_serie = cols_map.get('serie')
        c_num = cols_map.get('numero')
        
        if not (c_ruc and c_serie and c_num):
            return "Error: Columnas requeridas para agrupar: RUC_Proveedor, Serie, Numero"
            
        # Optional/Items
        c_sku = cols_map.get('productosku') or cols_map.get('sku')
        c_qty = cols_map.get('cantidad')
        c_price = cols_map.get('preciounitario') or cols_map.get('precio')
        c_fecha = cols_map.get('fecha')
        c_total = cols_map.get('total')
        c_moneda = cols_map.get('moneda')
        
        if not (c_sku and c_qty and c_price):
             return "Error: Columnas requeridas para items: ProductoSKU, Cantidad, PrecioUnitario"

        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Resolve Providers Cache
        cursor.execute("SELECT ruc_dni, id FROM proveedores")
        prov_map = dict(cursor.fetchall())
        
        # 2. Resolve Products Cache
        cursor.execute("SELECT codigo_sku, id FROM productos")
        prod_map = dict(cursor.fetchall())
        
        # 3. Get TC
        tc_actual = 3.75 # Default fallback
        try:
             tc_actual = obtener_tc_sunat()
        except: pass

        df['dummy'] = 1 # Helper for grouping is not strictly needed if we list group keys
        
        # Clean data for grouping
        # Handle Potential NaN in grouping keys
        df.dropna(subset=[c_ruc, c_serie, c_num], inplace=True)
        
        grouped = df.groupby([c_ruc, c_serie, c_num])
        
        processed_docs = 0
        errors = []
        
        # Start Transaction? SQLite default auto-transaction but let's be implicit.
        # But we commit inside loop for partial success? No, better atomic or partial? 
        # User experience: Partial success is often better for bulk loads unless strict transaction required.
        # I'll stick to partial success logging.
        
        for (ruc, serie, numero), group in grouped:
            try:
                # Resolve Provider
                ruc = str(ruc).strip()
                prov_id = prov_map.get(ruc)
                if not prov_id:
                    errors.append(f"Proveedor RUC {ruc} no existe/creado.")
                    continue
                
                # Header Info (Take first row)
                first = group.iloc[0]
                fecha = str(first[c_fecha]) if c_fecha else datetime.now().strftime("%Y-%m-%d")
                moneda = str(first[c_moneda]).strip() if c_moneda and pd.notna(first[c_moneda]) else 'PEN'
                
                # Check Duplicate
                cursor.execute("SELECT id FROM compras_cabecera WHERE proveedor_id=? AND serie=? AND numero=?", (prov_id, serie, numero))
                if cursor.fetchone():
                    errors.append(f"Factura {serie}-{numero} de RUC {ruc} ya existe.")
                    continue
                    
                # Build Items
                detalles = []
                calc_total = 0.0
                
                valid_items = True
                for idx, row in group.iterrows():
                    sku = str(row[c_sku]).strip()
                    pid = prod_map.get(sku)
                    if not pid:
                        errors.append(f"SKU {sku} en factura {serie}-{numero} no existe.")
                        valid_items = False
                        break
                        
                    qty = float(row[c_qty])
                    price = float(row[c_price])
                    
                    detalles.append({
                        "pid": pid,
                        "cantidad": qty,
                        "precio_unitario": price
                    })
                    calc_total += qty * price
                
                if not valid_items: continue
                
                base = round(calc_total / 1.18, 2)
                igv = round(calc_total - base, 2)
                
                cursor.execute("""
                    INSERT INTO compras_cabecera (
                        proveedor_id, fecha_emision, tipo_documento, serie, numero, 
                        moneda, total_compra, total_gravada, total_igv, tipo_cambio, fecha_registro
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (prov_id, fecha, 'FACTURA', serie, numero, moneda, calc_total, base, igv, tc_actual, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                compra_id = cursor.lastrowid
                
                for d in detalles:
                    pid = d['pid']
                    qty = d['cantidad']
                    price = d['precio_unitario']
                    
                    # Update Stock/Cost
                    cursor.execute("SELECT stock_actual, costo_promedio FROM productos WHERE id=?", (pid,))
                    p_row = cursor.fetchone()
                    st_old, cost_old = p_row if p_row else (0,0)
                    
                    new_st = st_old + qty
                    # Simplicity: Assume Input Price is in Moneda indicated.
                    price_pen = price * tc_actual if moneda == 'USD' else price
                    
                    if new_st > 0:
                        new_cost = ((st_old * cost_old) + (qty * price_pen)) / new_st
                    else:
                        new_cost = price_pen
                        
                    cursor.execute("UPDATE productos SET stock_actual=?, costo_promedio=? WHERE id=?", (new_st, new_cost, pid))
                    
                    # Insert Detail
                    cursor.execute("""
                        INSERT INTO compras_detalle (compra_id, producto_id, cantidad, precio_unitario, subtotal, almacen_id)
                        VALUES (?, ?, ?, ?, ?, 1)
                    """, (compra_id, pid, qty, price, qty*price))
                    
                    # Update Almacen 1
                    cursor.execute("SELECT id FROM stock_almacen WHERE producto_id=? AND almacen_id=1", (pid,))
                    sar = cursor.fetchone()
                    if sar:
                        cursor.execute("UPDATE stock_almacen SET stock_actual=stock_actual+? WHERE id=?", (qty, sar[0]))
                    else:
                        cursor.execute("INSERT INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, 1, ?)", (pid, qty))
                        
                processed_docs += 1
                conn.commit() # Commit per document
                
            except Exception as e:
                errors.append(f"Error procesando doc {serie}-{numero}: {str(e)}")
                # If error, the implicit transaction for this iteration (if any) rolls back? 
                # SQLite python driver is usually auto-commit? No. 
                # We committed above if successful. If error exception, we should probably rollback?
                # But rollback would rollback previous success if we didn't commit.
                # So we commit per document.
        
        msg = f"Procesadas {processed_docs} facturas."
        if errors:
            msg += f" Errores ({len(errors)}): {'; '.join(errors[:3])}..."
        return msg
        
    except Exception as e:
        if conn: conn.rollback()
        return f"Error global carga compras: {str(e)}"
    finally:
        if conn:
            try: conn.close()
            except: pass
