
import pandas as pd
from datetime import datetime
from src.database.db import get_connection

def listar_guias():
    conn = get_connection()
    try:
        query = """
            SELECT 
                g.id, 
                g.numero_guia, 
                g.serie,
                g.numero,
                CAST(g.fecha_recepcion AS TEXT) as fecha,
                p.razon_social as proveedor_nombre,
                g.oc_id,
                'OC-' || g.oc_id as documento_ref,
                (SELECT COUNT(*) FROM guias_remision_det WHERE guia_id = g.id) as items_count
            FROM guias_remision g
            LEFT JOIN proveedores p ON g.proveedor_id = p.id
            ORDER BY g.fecha_recepcion DESC
        """
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()

def obtener_guia(gid):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.*, p.razon_social, p.ruc_dni
            FROM guias_remision g
            LEFT JOIN proveedores p ON g.proveedor_id = p.id
            WHERE g.id = ?
        """, (gid,))
        row = cursor.fetchone()
        if not row: return None
        
        cols = [d[0] for d in cursor.description]
        cab = dict(zip(cols, row))
        
        cursor.execute("""
            SELECT gd.*, p.nombre as producto, p.codigo_sku as sku, p.unidad_medida, a.nombre as almacen
            FROM guias_remision_det gd
            JOIN productos p ON gd.producto_id = p.id
            LEFT JOIN almacenes a ON gd.almacen_destino_id = a.id
            WHERE gd.guia_id = ?
        """, (gid,))
        
        det_rows = cursor.fetchall()
        det_cols = [d[0] for d in cursor.description]
        detalles = [dict(zip(det_cols, r)) for r in det_rows]
        
        return {"cabecera": cab, "detalles": detalles}
    finally:
        conn.close()

def crear_guia_remision(data):
    """
    Crea una guía de remisión.
    data: {
        proveedor_id, oc_id, numero_guia, fecha_recepcion,
        items: [{pid, cantidad, almacen_id}]
    }
    Nota: Esto DEBERÍA afectar stock? 
    En muchos ERPs, la Guía de Remisión Ingreso AUMENTA el stock físico, y la Factura solo valoriza.
    Sin embargo, en este sistema simple, la FACTURA/COMPRA aumentaba el stock en `backend.py`.
    Si implementamos Guía, debemos decidir si la Guía mueve stock o la Factura.
    
    Revisando `backend.py.bak` (logic extracted manually earlier in inspection):
    La función `registrar_compra` aumentaba stock.
    No vimos lógica de stock en guias en `check_traceability`. 
    
    Asumiremos por ahora que la Guía es solo DOCUMENTARIA (Control), 
    y el stock se mueve con la Factura (Compra), para no duplicar stock
    si el usuario registra ambos.
    
    OJO: El usuario podría querer que la guía mueva stock. 
    Por seguridad en refactorización sin cambiar lógica de negocio profunda:
    Mantendremos que la Guía es Documentaria, salvo que veamos evidencia de lo contrario.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check duplicado
        cursor.execute("SELECT id FROM guias_remision WHERE numero_guia = ? AND proveedor_id = ?", 
                      (data['numero_guia'], data['proveedor_id']))
        if cursor.fetchone():
            return False, "Número de guía ya existe para este proveedor"

        cursor.execute("""
            INSERT INTO guias_remision (proveedor_id, oc_id, numero_guia, serie, numero, fecha_recepcion)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data['proveedor_id'], data.get('oc_id'), data['numero_guia'], data.get('serie'), data.get('numero'), data['fecha_recepcion']))
        
        guia_id = cursor.lastrowid
        
        for item in data['items']:
            cursor.execute("""
                INSERT INTO guias_remision_det (guia_id, producto_id, cantidad_recibida, almacen_destino_id)
                VALUES (?, ?, ?, ?)
            """, (guia_id, item['pid'], item['cantidad'], item.get('almacen_id', 1)))
            
        conn.commit()
        return True, "Guía registrada correctamente"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()
