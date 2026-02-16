import sqlite3
import os
import sys
import subprocess

def init_db(db_path):
    # Asegurar que el directorio de la base de datos exista
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        print(f"Creando directorio: {db_dir}")
        os.makedirs(db_dir)

    if os.path.exists(db_path):
        print(f"Aviso: La base de datos ya existe en {db_path}")
        confirm = input("¿Deseas sobrescribir la base de datos existente? (s/n): ").lower()
        if confirm != 's':
            print("Operación cancelada.")
            return
        try:
            os.remove(db_path)
        except Exception as e:
            print(f"Error al eliminar la base de datos existente: {e}")
            return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creando tablas...")
    try:
        cursor.execute('''CREATE TABLE almacenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                ubicacion TEXT
            )''')
        cursor.execute('''CREATE TABLE categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )''')
        cursor.execute('''CREATE TABLE compras_cabecera (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER NOT NULL,
                fecha_emision DATE NOT NULL,
                tipo_documento TEXT NOT NULL, -- FACTURA, BOLETA, ETC
                serie TEXT,
                numero TEXT,
                moneda TEXT DEFAULT 'PEN',
                total_gravada REAL DEFAULT 0,
                total_igv REAL DEFAULT 0,
                total_compra REAL NOT NULL,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP, tipo_cambio REAL DEFAULT 1.0, orden_compra_id INTEGER REFERENCES ordenes_compra(id),
                FOREIGN KEY (proveedor_id) REFERENCES proveedores (id)
            )''')
        cursor.execute('''CREATE TABLE compras_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compra_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                descripcion TEXT, -- Por si el nombre del producto cambia o es un servicio
                cantidad REAL NOT NULL,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL, unidad_medida TEXT DEFAULT 'UND', costo_previo REAL DEFAULT 0, tasa_impuesto REAL DEFAULT 18.0, almacen_id INTEGER DEFAULT 1,
                FOREIGN KEY (compra_id) REFERENCES compras_cabecera (id),
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )''')
        cursor.execute('''CREATE TABLE configuracion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clave TEXT UNIQUE NOT NULL,
                valor TEXT,
                descripcion TEXT,
                fecha_modificacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
        cursor.execute('''CREATE TABLE factura_guia_rel (
                factura_id INTEGER,
                guia_id INTEGER,
                PRIMARY KEY(factura_id, guia_id),
                FOREIGN KEY(factura_id) REFERENCES compras_cabecera(id),
                FOREIGN KEY(guia_id) REFERENCES guias_remision(id)
            )''')
        cursor.execute('''CREATE TABLE guias_remision (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER,
                oc_id INTEGER, -- Puede ser null si es entrada directa
                numero_guia TEXT,
                fecha_recepcion DATE,
                FOREIGN KEY(oc_id) REFERENCES ordenes_compra(id)
            )''')
        cursor.execute('''CREATE TABLE guias_remision_det (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guia_id INTEGER,
                producto_id INTEGER,
                cantidad_recibida REAL,
                almacen_destino_id INTEGER,
                FOREIGN KEY(guia_id) REFERENCES guias_remision(id),
                FOREIGN KEY(producto_id) REFERENCES productos(id)
            )''')
        cursor.execute('''CREATE TABLE ordenes_compra (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proveedor_id INTEGER,
                fecha_emision DATE,
                fecha_entrega_est DATE,
                estado TEXT DEFAULT 'PENDIENTE', -- PENDIENTE, PARCIAL, COMPLETADA, ANULADA
                moneda TEXT DEFAULT 'PEN',
                observaciones TEXT, total_orden REAL DEFAULT 0, tasa_igv REAL DEFAULT 18.0, direccion_entrega TEXT,
                FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
            )''')
        cursor.execute('''CREATE TABLE ordenes_compra_det (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oc_id INTEGER,
                producto_id INTEGER,
                cantidad_solicitada REAL,
                cantidad_recibida REAL DEFAULT 0,
                precio_unitario_pactado REAL,
                FOREIGN KEY(oc_id) REFERENCES ordenes_compra(id),
                FOREIGN KEY(producto_id) REFERENCES productos(id)
            )''')
        cursor.execute('''CREATE TABLE ordenes_compra_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                orden_id INTEGER,
                producto_id INTEGER,
                cantidad REAL,
                precio_unitario REAL,
                FOREIGN KEY (orden_id) REFERENCES ordenes_compra (id),
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )''')
        cursor.execute('''CREATE TABLE productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_sku TEXT UNIQUE,
                nombre TEXT NOT NULL,
                unidad_medida TEXT NOT NULL,
                categoria TEXT,
                stock_actual REAL DEFAULT 0,
                costo_promedio REAL DEFAULT 0
            , precio_venta REAL DEFAULT 0, categoria_id INTEGER DEFAULT 1 REFERENCES categorias(id), stock_minimo REAL DEFAULT 0)''')
        cursor.execute('''CREATE TABLE proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ruc_dni TEXT UNIQUE NOT NULL,
                razon_social TEXT NOT NULL,
                direccion TEXT,
                telefono TEXT,
                email TEXT
            , categoria TEXT DEFAULT 'General')''')
        cursor.execute('''CREATE TABLE salidas_cabecera (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                tipo_salida TEXT DEFAULT 'Venta',
                destino TEXT,
                observaciones TEXT,
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
        cursor.execute('''CREATE TABLE salidas_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                salida_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad REAL NOT NULL,
                almacen_id INTEGER DEFAULT 1,
                costo_unitario REAL DEFAULT 0,
                FOREIGN KEY (salida_id) REFERENCES salidas_cabecera(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )''')
        cursor.execute('''CREATE TABLE stock_almacen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER,
                almacen_id INTEGER,
                stock_actual REAL DEFAULT 0,
                FOREIGN KEY(producto_id) REFERENCES productos(id),
                FOREIGN KEY(almacen_id) REFERENCES almacenes(id)
            )''')
        cursor.execute('''CREATE TABLE tipo_cambio (fecha TEXT PRIMARY KEY, venta REAL, compra REAL, origen TEXT)''')
        cursor.execute('''CREATE TABLE traslados_cabecera (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE,
            origen_id INTEGER,
            destino_id INTEGER,
            observaciones TEXT,
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
            estado TEXT DEFAULT 'COMPLETADO',
            FOREIGN KEY(origen_id) REFERENCES almacenes(id),
            FOREIGN KEY(destino_id) REFERENCES almacenes(id)
        )''')
        cursor.execute('''CREATE TABLE traslados_detalle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            traslado_id INTEGER,
            producto_id INTEGER,
            cantidad REAL,
            costo_unitario REAL,
            FOREIGN KEY(traslado_id) REFERENCES traslados_cabecera(id),
            FOREIGN KEY(producto_id) REFERENCES productos(id)
        )''')
        cursor.execute('''CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            , username_hash TEXT, username_encrypted TEXT)''')

        conn.commit()
        print("Schema de base de datos inicializado con éxito.")
        
        # Preguntar por datos de prueba
        confirm_seed = input("¿Deseas cargar datos de prueba iniciales? (s/n): ").lower()
        if confirm_seed == 's':
            scripts_dir = os.path.dirname(os.path.abspath(__file__))
            seed_script = os.path.join(scripts_dir, "seed_data_v2.py")
            if os.path.exists(seed_script):
                print("Ejecutando carga de datos de prueba...")
                # Usar el mismo ejecutable de python actual
                subprocess.run([sys.executable, seed_script], check=True)
            else:
                print(f"Error: No se encontró el script de semillas en {seed_script}")

    except Exception as e:
        print(f"Error creando el schema: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # Definir ruta por defecto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    default_db_path = os.path.join(project_root, "data", "gestion_basica.db")

    if len(sys.argv) < 2:
        print(f"Usando ruta por defecto: {default_db_path}")
        db_path = default_db_path
    else:
        db_path = sys.argv[1]
    
    init_db(db_path)
