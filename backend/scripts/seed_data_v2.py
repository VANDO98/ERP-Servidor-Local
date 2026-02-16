import sys
import os
import sqlite3
import random
from datetime import datetime, timedelta
import hashlib

# Add backend directory to path to import src modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

def get_password_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_username_hash(username):
    return hashlib.sha256(username.encode()).hexdigest()

def encrypt_username(username):
    return username # No encryption for seed

DB_PATH = os.path.join(backend_dir, "data", "gestion_basica.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def clear_database():
    print("🧹 Cleaning database...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")
    tables = [
        "traslados_detalle", "traslados_cabecera", "salidas_detalle", "salidas_cabecera",
        "factura_guia_rel", "guias_remision_det", "guias_remision", "compras_detalle",
        "compras_cabecera", "ordenes_compra_det", "ordenes_compra_detalle", "ordenes_compra",
        "stock_almacen", "productos", "proveedores", "categorias", "almacenes",
        "users", "configuracion", "tipo_cambio"
    ]
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        except sqlite3.OperationalError: pass
    conn.commit()
    conn.close()
    print("✅ Database cleared.")

def seed_users():
    print("👤 Creating Admin User...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (username, password_hash, role, is_active, username_hash, username_encrypted)
        VALUES ('admin', ?, 'admin', 1, ?, 'admin')
    """, (get_password_hash("admin"), get_username_hash("admin")))
    conn.commit()
    conn.close()

def seed_config_and_tc():
    print("⚙️ Seeding Configuration and Exchange Rates...")
    conn = get_connection()
    cursor = conn.cursor()
    
    configs = [
        ('EMPRESA_NOMBRE', 'CORPORACION FERRETERA PANDO SAC', 'Nombre legal de la empresa'),
        ('EMPRESA_RUC', '20123456789', 'RUC de la empresa'),
        ('MONEDA_PRINCIPAL', 'PEN', 'Moneda base del sistema'),
        ('IGV_TASA', '18.0', 'Tasa de impuesto actual'),
        ('ALMACEN_DEFECTO', '1', 'ID del almacén principal')
    ]
    cursor.executemany("INSERT INTO configuracion (clave, valor, descripcion) VALUES (?, ?, ?)", configs)
    
    start_date = datetime.now() - timedelta(days=90)
    tc_data = []
    for i in range(91):
        fecha = (start_date + timedelta(days=i)).date().isoformat()
        venta = round(3.70 + (random.random() * 0.15), 3)
        compra = round(venta - 0.02, 3)
        tc_data.append((fecha, venta, compra, 'API_SUNAT_SIM'))
    cursor.executemany("INSERT INTO tipo_cambio (fecha, venta, compra, origen) VALUES (?, ?, ?, ?)", tc_data)
    
    conn.commit()
    conn.close()

def seed_master_data():
    print("📦 Seeding Master Data...")
    conn = get_connection()
    cursor = conn.cursor()
    
    almacenes = [(1, "Almacén Principal", "Lima - Central"), (2, "Almacén Secundario", "Callao - Puerto"), (3, "Almacén Norte", "Los Olivos")]
    cursor.executemany("INSERT OR REPLACE INTO almacenes (id, nombre, ubicacion) VALUES (?, ?, ?)", almacenes)
    
    categorias = [(1, "Materiales"), (2, "Acabados"), (3, "Herramientas"), (4, "EPP"), (5, "Oficina"), (6, "Electricidad"), (7, "Gasfitería"), (8, "Iluminación"), (9, "Maderas"), (10, "Ferretería General")]
    cursor.executemany("INSERT OR REPLACE INTO categorias (id, nombre) VALUES (?, ?)", categorias)
    
    proveedores = [
        ("20100123456", "CONSTRUCTORA SOL", "Av. Principal 123", "999888777", "ventas@sol.com", "Materiales"),
        ("20200987654", "TIENDAS INDUSTRIALES", "Jr. Los Andes 456", "999111222", "contacto@tiendas.com", "Herramientas"),
        ("20300456789", "PINTURAS COLOR", "Av. Colorida 789", "987654321", "ventas@color.com", "Acabados"),
        ("20400112233", "SAFE WORK PERU", "Calle Seguridad 101", "988777666", "ventas@safework.pe", "EPP"),
        ("20555666777", "ELECTRO HOME", "Av. La Luz 2020", "911222333", "info@electrohome.com", "Electricidad")
    ]
    cursor.executemany("INSERT INTO proveedores (ruc_dni, razon_social, direccion, telefono, email, categoria) VALUES (?, ?, ?, ?, ?, ?)", proveedores)
    
    productos = [
        ("CEMENTO-SOL", "CEMENTO SOL TIPO I", "BOLSA", 1, 30.0, 28.0), ("FIERRO-1/2", "FIERRO CORRUGADO 1/2", "UND", 1, 38.0, 35.0),
        ("PINT-VENC-BL", "PINTURA VENCEDOR BL", "BALDE", 2, 85.0, 75.0), ("MARTILLO-ST", "MARTILLO STANLEY", "UND", 3, 45.0, 35.0),
        ("CASCO-SEG", "CASCO SEGURIDAD", "UND", 4, 15.0, 10.0), ("CABLE-12", "CABLE 12AWG", "ROLLO", 6, 150.0, 120.0),
        ("TUBO-PVC", "TUBO PVC 1/2", "UND", 7, 10.0, 7.0), ("FOCO-LED", "FOCO LED 9W", "UND", 8, 8.0, 5.0),
        ("TRIPLAY-4", "TRIPLAY 4MM", "PLANCHA", 9, 45.0, 38.0), ("PEGAMENTO", "PEGAMENTO PVC", "UND", 10, 12.0, 8.0)
    ]
    cursor.executemany("INSERT INTO productos (codigo_sku, nombre, unidad_medida, categoria_id, precio_venta, costo_promedio, stock_actual, stock_minimo) VALUES (?, ?, ?, ?, ?, ?, 0, 20)", productos)
    
    conn.commit()
    conn.close()

def generate_full_transactions():
    print("🔄 Generating Transactions & Delivery Guides...")
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM productos"); prod_ids = [r[0] for r in cursor.fetchall()]
    cursor.execute("SELECT id FROM proveedores"); prov_ids = [r[0] for r in cursor.fetchall()]
    cursor.execute("SELECT id FROM almacenes"); alm_ids = [r[0] for r in cursor.fetchall()]
    
    start_date = datetime.now() - timedelta(days=90)
    
    # 1. Órdenes de Compra (OC)
    print("  - Orders...")
    for i in range(15):
        fecha = start_date + timedelta(days=random.randint(0, 80))
        prov_id = random.choice(prov_ids)
        estado = random.choice(['PENDIENTE', 'ATENDIDO', 'PARCIAL', 'COMPLETADA'])
        cursor.execute("INSERT INTO ordenes_compra (proveedor_id, fecha_emision, estado, moneda) VALUES (?, ?, ?, 'PEN')", (prov_id, fecha.strftime("%Y-%m-%d"), estado))
        oc_id = cursor.lastrowid
        
        p_id = random.choice(prod_ids)
        qty = random.randint(50, 200)
        cursor.execute("INSERT INTO ordenes_compra_det (oc_id, producto_id, cantidad_solicitada, precio_unitario_pactado) VALUES (?, ?, ?, ?)", (oc_id, p_id, qty, 25.0))
        cursor.execute("INSERT INTO ordenes_compra_detalle (orden_id, producto_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)", (oc_id, p_id, qty, 25.0))

    # 2. Guías de Remisión
    print("  - Delivery Guides...")
    cursor.execute("SELECT id, proveedor_id FROM ordenes_compra")
    ocs = cursor.fetchall()
    for oc_id, prov_id in ocs[:10]:
        fecha = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO guias_remision (proveedor_id, oc_id, numero_guia, fecha_recepcion) VALUES (?, ?, ?, ?)", 
                       (prov_id, oc_id, f"GR{random.randint(100,999)}-{random.randint(1000,9999)}", fecha))
        guia_id = cursor.lastrowid
        
        cursor.execute("SELECT producto_id, cantidad_solicitada FROM ordenes_compra_det WHERE oc_id = ?", (oc_id,))
        oc_item = cursor.fetchone()
        if oc_item:
            cursor.execute("INSERT INTO guias_remision_det (guia_id, producto_id, cantidad_recibida, almacen_destino_id) VALUES (?, ?, ?, 1)", 
                           (guia_id, oc_item[0], oc_item[1]))

    # 3. Compras (Facturas)
    print("  - Purchases & Links...")
    for i in range(40):
        fecha = start_date + timedelta(days=random.randint(5, 88))
        prov_id = random.choice(prov_ids)
        
        p_id = random.choice(prod_ids)
        qty = random.randint(10, 50)
        cost = 25.0
        total = round(qty * cost, 2)
        base = round(total / 1.18, 2)
        igv = round(total - base, 2)
        
        cursor.execute("""
            INSERT INTO compras_cabecera (proveedor_id, fecha_emision, tipo_documento, serie, numero, moneda, total_compra, total_gravada, total_igv, tipo_cambio)
            VALUES (?, ?, 'FACTURA', 'F001', ?, 'PEN', ?, ?, ?, 3.75)
        """, (prov_id, fecha.strftime("%Y-%m-%d"), f"{random.randint(10000,99999)}", total, base, igv))
        compra_id = cursor.lastrowid
        
        if i % 2 == 0:
            cursor.execute("SELECT id FROM guias_remision ORDER BY RANDOM() LIMIT 1")
            g_row = cursor.fetchone()
            if g_row:
                cursor.execute("INSERT INTO factura_guia_rel (factura_id, guia_id) VALUES (?, ?)", (compra_id, g_row[0]))
        
        cursor.execute("INSERT INTO compras_detalle (compra_id, producto_id, cantidad, precio_unitario, subtotal, almacen_id) VALUES (?, ?, ?, ?, ?, 1)", (compra_id, p_id, qty, cost, total))
        cursor.execute("UPDATE productos SET stock_actual = stock_actual + ? WHERE id = ?", (qty, p_id))
        cursor.execute("INSERT OR REPLACE INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, 1, (SELECT COALESCE(stock_actual,0) + ? FROM stock_almacen WHERE producto_id=? AND almacen_id=1))", (p_id, qty, p_id))

    # 4. Salidas y Traslados
    print("  - Exits & Transfers...")
    for i in range(20):
        fecha = start_date + timedelta(days=random.randint(10, 90))
        cursor.execute("INSERT INTO salidas_cabecera (fecha, tipo_salida, observaciones) VALUES (?, 'CONSUMO', 'Urgencia')", (fecha.strftime("%Y-%m-%d"),))
        s_id = cursor.lastrowid
        p_id = random.choice(prod_ids)
        cursor.execute("INSERT INTO salidas_detalle (salida_id, producto_id, cantidad, almacen_id) VALUES (?, ?, 5, 1)", (s_id, p_id))
        cursor.execute("UPDATE productos SET stock_actual = stock_actual - 5 WHERE id = ?", (p_id,))
    
    for i in range(5):
        cursor.execute("INSERT INTO traslados_cabecera (fecha, origen_id, destino_id, estado) VALUES ('2026-02-15', 1, 2, 'COMPLETADO')")
        t_id = cursor.lastrowid
        cursor.execute("INSERT INTO traslados_detalle (traslado_id, producto_id, cantidad) VALUES (?, ?, 10)", (t_id, random.choice(prod_ids)))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    try:
        clear_database()
        seed_users()
        seed_config_and_tc()
        seed_master_data()
        generate_full_transactions()
        print("🚀 Base de Datos completamente poblada (TODAS las tablas)!")
    except Exception as e: print(f"❌ Error: {e}")
