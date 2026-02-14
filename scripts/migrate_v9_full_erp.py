import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gestion_basica.db")

def migrate_full_erp():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        print("🏗️ Iniciando Migración a ERP Logístico Completo (Fase 9 & 10)...")
        
        # --- 1. WMS (Multi-Almacén) ---
        print("- Creando tablas WMS...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS almacenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                ubicacion TEXT
            )
        """)
        
        # Insertar Almacén Principal por defecto
        cursor.execute("SELECT COUNT(*) FROM almacenes")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO almacenes (nombre, ubicacion) VALUES ('Almacén Principal', 'Sede Central')")
            main_warehouse_id = cursor.lastrowid
        else:
            cursor.execute("SELECT id FROM almacenes WHERE nombre LIKE 'Almacén Principal%' LIMIT 1")
            res = cursor.fetchone()
            main_warehouse_id = res[0] if res else 1

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_almacen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER,
                almacen_id INTEGER,
                stock_actual REAL DEFAULT 0,
                FOREIGN KEY(producto_id) REFERENCES productos(id),
                FOREIGN KEY(almacen_id) REFERENCES almacenes(id)
            )
        """)
        
        # Migrar Stock Global -> Stock Almacén Principal
        # Verificar si columna stock_actual existe en productos (para no migrar doble)
        # SQLite no permite drop column fácil, así que mantenemos la columna por ahora pero la ignoramos en lógica futura
        print("- Migrando stock existente...")
        cursor.execute("SELECT id, stock_actual FROM productos")
        prods = cursor.fetchall()
        for pid, stock in prods:
            # Check if exists in stock_almacen
            cursor.execute("SELECT id FROM stock_almacen WHERE producto_id = ? AND almacen_id = ?", (pid, main_warehouse_id))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, ?, ?)", (pid, main_warehouse_id, stock))
        
        # --- 2. SALIDAS (Servicios / Ventas) ---
        print("- Creando tablas Salidas...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS salidas_cabecera (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE,
                tipo_movimiento TEXT, -- 'VENTA', 'SERVICIO', 'MERMA'
                destino_nombre TEXT, -- Cliente o Proyecto
                observaciones TEXT,
                usuario_id INTEGER
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS salidas_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                salida_id INTEGER,
                producto_id INTEGER,
                almacen_origen_id INTEGER,
                cantidad REAL,
                precio_venta REAL, -- Opcional, si es venta
                FOREIGN KEY(salida_id) REFERENCES salidas_cabecera(id),
                FOREIGN KEY(producto_id) REFERENCES productos(id)
            )
        """)

        # --- 3. APROVISIONAMIENTO (OC -> Guía -> Factura) ---
        print("- Creando tablas Aprovisionamiento...")
        
        # Orden de Compra
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ordenes_compra (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER,
                fecha_emision DATE,
                fecha_entrega_est DATE,
                estado TEXT DEFAULT 'PENDIENTE', -- PENDIENTE, PARCIAL, COMPLETADA, ANULADA
                moneda TEXT DEFAULT 'PEN',
                observaciones TEXT,
                FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ordenes_compra_det (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oc_id INTEGER,
                producto_id INTEGER,
                cantidad_solicitada REAL,
                cantidad_recibida REAL DEFAULT 0,
                precio_unitario_pactado REAL,
                FOREIGN KEY(oc_id) REFERENCES ordenes_compra(id),
                FOREIGN KEY(producto_id) REFERENCES productos(id)
            )
        """)
        
        # Guías de Remisión (Entrada)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guias_remision (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER,
                oc_id INTEGER, -- Puede ser null si es entrada directa
                numero_guia TEXT,
                fecha_recepcion DATE,
                FOREIGN KEY(oc_id) REFERENCES ordenes_compra(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guias_remision_det (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guia_id INTEGER,
                producto_id INTEGER,
                cantidad_recibida REAL,
                almacen_destino_id INTEGER,
                FOREIGN KEY(guia_id) REFERENCES guias_remision(id),
                FOREIGN KEY(producto_id) REFERENCES productos(id)
            )
        """)
        
        # Relación Factura (Compras Cabecera) <-> Guías
        # Una factura puede pagar items de varias guías (o viceversa parcial)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS factura_guia_rel (
                factura_id INTEGER,
                guia_id INTEGER,
                PRIMARY KEY(factura_id, guia_id),
                FOREIGN KEY(factura_id) REFERENCES compras_cabecera(id),
                FOREIGN KEY(guia_id) REFERENCES guias_remision(id)
            )
        """)

        conn.commit()
        print("✅ Migración Completa.")
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_full_erp()
