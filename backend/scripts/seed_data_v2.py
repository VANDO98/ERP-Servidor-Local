import sys
import os
import sqlite3
import random
from datetime import datetime, timedelta

# Add backend directory to path to import src modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.append(backend_dir)

# from src.auth import get_password_hash, get_username_hash, encrypt_username
# SIMPLIFIED HASHING FOR SEEDING ONLY (To avoid dependencies)
import hashlib

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
    
    # Disable foreign keys temporarily
    cursor.execute("PRAGMA foreign_keys = OFF;")
    
    tables = [
        "traslados_detalle", "traslados_cabecera",
        "salidas_detalle", "salidas_cabecera",
        "factura_guia_rel", "guias_remision_det", "guias_remision",
        "compras_detalle", "compras_cabecera",
        "ordenes_compra_det", "ordenes_compra",
        "stock_almacen",
        "productos",
        "proveedores",
        "categorias",
        "almacenes",
        "users",
        "configuracion"
    ]
    
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
            # Reset auto-increment
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")
        except sqlite3.OperationalError:
            pass # Table might not exist
            
    conn.commit()
    conn.close()
    print("✅ Database cleared.")

def seed_users():
    print("👤 Creating Admin User...")
    conn = get_connection()
    cursor = conn.cursor()
    
    password = "admin"
    pwd_hash = get_password_hash(password)
    username = "admin"
    u_hash = get_username_hash(username)
    u_enc = encrypt_username(username)
    
    cursor.execute("""
        INSERT INTO users (username, password_hash, role, is_active, username_hash, username_encrypted)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, pwd_hash, 'admin', 1, u_hash, u_enc))
    
    conn.commit()
    conn.close()

def seed_master_data():
    print("📦 Seeding Master Data...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Almacenes
    almacenes = [
        (1, "Almacén Principal", "Lima - Central"),
        (2, "Almacén Secundario", "Callao - Puerto")
    ]
    cursor.executemany("INSERT INTO almacenes (id, nombre, ubicacion) VALUES (?, ?, ?)", almacenes)
    
    # 2. Categorias
    categorias = [
        (1, "Materiales de Construcción"),
        (2, "Acabados y Pintura"),
        (3, "Herramientas Manuales"),
        (4, "EPP / Seguridad"),
        (5, "Oficina y Útiles"),
        (6, "Electricidad"),
        (7, "Gasfitería")
    ]
    cursor.executemany("INSERT INTO categorias (id, nombre) VALUES (?, ?)", categorias)
    
    # 3. Proveedores
    proveedores = [
        ("20100123456", "CONSTRUCTORA Y FERRETERIA SOL", "Av. Principal 123", "999888777", "ventas@sol.com", "Materiales"),
        ("20200987654", "TIENDAS INDUSTRIALES SAC", "Jr. Los Andes 456", "999111222", "contacto@tiendas.com", "Herramientas"),
        ("20300456789", "DISTRIBUIDORA PINTURAS COLOR", "Av. Colorida 789", "987654321", "ventas@color.com", "Acabados"),
        ("20400112233", "SAFE WORK PERU SRL", "Calle Seguridad 101", "988777666", "ventas@safework.pe", "EPP"),
        ("20555666777", "ELECTRO HOME S.A.", "Av. La Luz 2020", "911222333", "info@electrohome.com", "Electricidad"),
        ("20600998877", "PLASTICOS Y TUBERIAS LIMA", "Zona Industrial Mz A", "966555444", "ventas@plasticoslima.com", "Gasfitería")
    ]
    cursor.executemany("INSERT INTO proveedores (ruc_dni, razon_social, direccion, telefono, email, categoria) VALUES (?, ?, ?, ?, ?, ?)", proveedores)
    
    # 4. Productos
    productos = [
        # Mat. Construcción
        ("CEMENTO-SOL", "CEMENTO SOL TIPO I", "BOLSA", 1, 30.00, 28.00),
        ("LADRILLO-KK", "LADRILLO KING KONG 18 HUECOS", "MILLAR", 1, 850.00, 800.00),
        ("FIERRO-1/2", "VARILLA FIERRO CORRUGADO 1/2", "UND", 1, 38.00, 35.00),
        ("ARENA-GRUESA", "ARENA GRUESA (M3)", "M3", 1, 45.00, 40.00),
        
        # Acabados
        ("PINT-VENC-BL", "PINTURA LATEX VENCEDOR BLANCO", "BALDE", 2, 85.00, 75.00),
        ("THINNER-ACR", "THINNER ACRILICO", "GALON", 2, 25.00, 20.00),
        ("BROCHA-4", "BROCHA CERDA FINA 4 PULG", "UND", 2, 12.00, 8.00),
        
        # Herramientas
        ("ALICATE-UNIV", "ALICATE UNIVERSAL 8 PULG", "UND", 3, 25.00, 18.00),
        ("MARTILLO-CARP", "MARTILLO CARPINTERO STANLEY", "UND", 3, 45.00, 35.00),
        ("DEST-PHILIPS", "DESTORNILLADOR PHILIPS 6X100", "UND", 3, 15.00, 10.00),
        
        # EPP
        ("CASCO-SEG-AM", "CASCO SEGURIDAD AMARILLO", "UND", 4, 15.00, 10.00),
        ("GUANTE-CUERO", "GUANTES DE CUERO REFORZADO", "PAR", 4, 18.00, 12.00),
        ("LENTES-PROT", "LENTES SEGURIDAD TRANSPARENTE", "UND", 4, 8.00, 5.00),
        
        # Oficina
        ("PAPEL-BOND", "PAPEL BOND A4 75GR", "PAQUETE", 5, 18.00, 14.00),
        
        # Electricidad
        ("CABLE-12AWG", "CABLE ELECTRICO 12AWG (ROLLO 100M)", "ROLLO", 6, 150.00, 120.00),
        ("INTERRUPTOR-D", "INTERRUPTOR DOBLE EMPOTRABLE", "UND", 6, 12.00, 8.00),
        
        # Gasfiteria
        ("TUBO-PVC-1/2", "TUBO PVC AGUA 1/2 PULG", "UND", 7, 10.00, 7.00),
        ("CODO-PVC-1/2", "CODO PVC 90 AGUA 1/2 PULG", "UND", 7, 2.00, 1.00)
    ]
    
    # Prepare inserts
    cursor.executemany("""
        INSERT INTO productos (codigo_sku, nombre, unidad_medida, categoria_id, precio_venta, costo_promedio, stock_actual, stock_minimo) 
        VALUES (?, ?, ?, ?, ?, ?, 0, 10)
    """, [(p[0], p[1], p[2], p[3], p[4], p[5]) for p in productos])
    
    conn.commit()
    conn.close()

def generate_transactions():
    print("🔄 Generating Transactions (Purchases, Inventory, Orders)...")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Fetch IDs
    cursor.execute("SELECT id FROM productos")
    prod_ids = [r[0] for r in cursor.fetchall()]
    
    cursor.execute("SELECT id FROM proveedores")
    prov_ids = [r[0] for r in cursor.fetchall()]
    
    if not prod_ids or not prov_ids:
        print("Error: Missing master data for transactions")
        return
        
    start_date = datetime.now() - timedelta(days=90)
    
    # 1. Purchases (Stock In)
    print("  - Generating Purchases...")
    
    for i in range(20): # 20 historical purchases
        fecha = start_date + timedelta(days=random.randint(0, 85))
        prov_id = random.choice(prov_ids)
        serie = f"F{random.randint(1,9)}01"
        numero = f"{random.randint(1, 9999):06d}"
        moneda = random.choice(['PEN', 'PEN', 'PEN', 'USD']) # Mostly PEN
        tc = 3.75 + (random.random() * 0.10)
        
        # Items for this purchase
        items_count = random.randint(2, 6)
        compra_items = random.sample(prod_ids, items_count)
        
        total_compra = 0
        detalles = []
        
        # Insert Header (Provisional Total)
        cursor.execute("""
            INSERT INTO compras_cabecera (proveedor_id, fecha_emision, tipo_documento, serie, numero, moneda, tipo_cambio, total_compra, fecha_registro, total_gravada, total_igv)
            VALUES (?, ?, 'FACTURA', ?, ?, ?, ?, 0, ?, 0, 0)
        """, (prov_id, fecha.strftime("%Y-%m-%d"), serie, numero, moneda, tc, datetime.now()))
        
        compra_id = cursor.lastrowid
        
        for pid in compra_items:
            # Get cost ref
            cursor.execute("SELECT costo_promedio FROM productos WHERE id=?", (pid,))
            costo_ref = cursor.fetchone()[0]
            
            qty = random.randint(10, 100)
            
            # Add some variance to price
            precio_unit = costo_ref * (0.9 + (random.random() * 0.2)) # +/- 10%
            if moneda == 'USD':
                precio_unit /= tc
                
            subtotal = qty * precio_unit
            total_compra += subtotal
            
            # Insert Detail
            cursor.execute("""
                INSERT INTO compras_detalle (compra_id, producto_id, cantidad, precio_unitario, subtotal, almacen_id)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (compra_id, pid, qty, precio_unit, subtotal))
            
            # Update Stock
            cursor.execute("UPDATE productos SET stock_actual = stock_actual + ? WHERE id = ?", (qty, pid))
            
            # Update Stock Almacen (Default 1)
            cursor.execute("SELECT id, stock_actual FROM stock_almacen WHERE producto_id=? AND almacen_id=1", (pid,))
            row_stock = cursor.fetchone()
            if row_stock:
                cursor.execute("UPDATE stock_almacen SET stock_actual = stock_actual + ? WHERE id=?", (qty, row_stock[0]))
            else:
                cursor.execute("INSERT INTO stock_almacen (producto_id, almacen_id, stock_actual) VALUES (?, 1, ?)", (pid, qty))
                
        # Update Header Total
        base = total_compra / 1.18
        igv = total_compra - base
        cursor.execute("UPDATE compras_cabecera SET total_compra=?, total_gravada=?, total_igv=? WHERE id=?", (total_compra, base, igv, compra_id))

    # 2. Exits (Stock Out)
    print("  - Generating Exits...")
    for i in range(15):
        fecha = start_date + timedelta(days=random.randint(10, 90))
        
        cursor.execute("""
            INSERT INTO salidas_cabecera (fecha, tipo_salida, destino, observaciones, fecha_registro)
            VALUES (?, 'CONSUMO', 'Obra Principal', 'Salida generada automaticamente', ?)
        """, (fecha.strftime("%Y-%m-%d"), datetime.now()))
        salida_id = cursor.lastrowid
        
        # Pick items that have stock
        cursor.execute("SELECT id, stock_actual FROM productos WHERE stock_actual > 10")
        available_prods = cursor.fetchall()
        
        if available_prods:
            salida_items = random.sample(available_prods, min(len(available_prods), random.randint(1, 4)))
            
            for pid, stock in salida_items:
                qty_out = random.randint(1, int(stock * 0.3)) # Take up to 30% of stock
                
                cursor.execute("""
                    INSERT INTO salidas_detalle (salida_id, producto_id, cantidad, almacen_id)
                    VALUES (?, ?, ?, 1)
                """, (salida_id, pid, qty_out))
                
                # Update Stock
                cursor.execute("UPDATE productos SET stock_actual = stock_actual - ? WHERE id = ?", (qty_out, pid))
                cursor.execute("UPDATE stock_almacen SET stock_actual = stock_actual - ? WHERE producto_id=? AND almacen_id=1", (qty_out, pid))

    # 3. Create active Purchase Orders (Pendientes)
    print("  - Generating Purchase Orders...")
    for i in range(3):
        fecha = datetime.now()
        prov_id = random.choice(prov_ids)
        
        cursor.execute("""
            INSERT INTO ordenes_compra (proveedor_id, fecha_emision, fecha_entrega_est, estado, moneda, observaciones, tasa_igv)
            VALUES (?, ?, ?, 'PENDIENTE', 'PEN', 'Orden generada automaticamente', 18.0)
        """, (prov_id, fecha.strftime("%Y-%m-%d"), (fecha + timedelta(days=7)).strftime("%Y-%m-%d")))
        oc_id = cursor.lastrowid
        
        oc_items = random.sample(prod_ids, 2)
        total_orden = 0
        for pid in oc_items:
             cursor.execute("SELECT costo_promedio FROM productos WHERE id=?", (pid,))
             costo = cursor.fetchone()[0]
             cantidad = random.randint(10, 50)
             subtotal = cantidad * costo
             total_orden += subtotal
             
             cursor.execute("""
                INSERT INTO ordenes_compra_det (oc_id, producto_id, cantidad_solicitada, precio_unitario_pactado)
                VALUES (?, ?, ?, ?)
             """, (oc_id, pid, cantidad, costo))
        
        # Update Header with Total
        cursor.execute("UPDATE ordenes_compra SET total_orden = ? WHERE id = ?", (total_orden, oc_id))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    try:
        clear_database()
        seed_users()
        seed_master_data()
        generate_transactions()
        print("🚀 Database reset and seeded successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
