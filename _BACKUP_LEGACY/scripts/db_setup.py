import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gestion_basica.db")

def create_connection():
    try:
        conn = sqlite3.connect(DB_NAME)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return None

def create_tables(conn):
    try:
        cursor = conn.cursor()
        
        # 1. Proveedores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proveedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ruc_dni TEXT UNIQUE NOT NULL,
                razon_social TEXT NOT NULL,
                direccion TEXT,
                telefono TEXT,
                email TEXT
            )
        """)
        
        # 2. Productos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_sku TEXT UNIQUE,
                nombre TEXT NOT NULL,
                unidad_medida TEXT NOT NULL,
                categoria TEXT,
                stock_actual REAL DEFAULT 0,
                costo_promedio REAL DEFAULT 0,
                precio_venta REAL DEFAULT 0
            )
        """)
        
        # 3. Compras Cabecera
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compras_cabecera (
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
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (proveedor_id) REFERENCES proveedores (id)
            )
        """)
        
        # 4. Compras Detalle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compras_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                compra_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                descripcion TEXT, -- Por si el nombre del producto cambia o es un servicio
                cantidad REAL NOT NULL,
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (compra_id) REFERENCES compras_cabecera (id),
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        """)
        
        print("Tablas creadas exitosamente.")
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    if not os.path.exists(DB_NAME):
        print(f"Creando base de datos: {DB_NAME}")
    else:
        print(f"La base de datos {DB_NAME} ya existe, verificando tablas...")
        
    conn = create_connection()
    if conn:
        create_tables(conn)
        conn.close()
