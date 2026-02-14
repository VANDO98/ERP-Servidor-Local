# Funciones de historial de salidas para agregar al backend.py

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
    """Retorna detalle completo de todas las salidas"""
    conn = get_connection()
    query = """
        SELECT 
            s.id as salida_id,
            s.fecha as Fecha,
            s.tipo_salida as Tipo,
            s.destino as Destino,
            p.codigo_sku as SKU,
            p.nombre as Producto,
            sd.cantidad as Cantidad,
            p.unidad_medida as UM,
            sd.costo_unitario as CostoUnit,
            (sd.cantidad * sd.costo_unitario) as ValorTotal
        FROM salidas_cabecera s
        JOIN salidas_detalle sd ON s.id = sd.salida_id
        JOIN productos p ON sd.producto_id = p.id
        ORDER BY s.fecha DESC, s.id DESC, p.nombre
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df
