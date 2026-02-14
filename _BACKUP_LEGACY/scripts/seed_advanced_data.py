
import sqlite3
import os
import random
from datetime import date, timedelta
import math

# --- CONFIGURACION ---
DAYS_HISTORY = 365
PERCENT_PURCHASE_CHANCE_DAILY = 0.4
TC_MEAN = 3.75
TC_STD = 0.05
IGV_RATE = 18.0

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gestion_basica.db")

PROVEEDORES_SEED = [
    # RUC, RS, Dir, Tel, Email
    ("20100055511", "ACEROS AREQUIPA S.A.", "Av. Enrique Meiggs 297, Callao", "999-111-222", "ventas@aceros.pe"),
    ("20503840123", "SODIMAC PERU S.A.", "Av. Javier Prado Este 1059", "999-333-444", "contacto@sodimac.com.pe"),
    ("20600012345", "FERRETERIA EL TORNILLO SAC", "Jr. Puno 123", "999-555-666", "ventas@tornillo.com"),
    ("20456789012", "PROMART HOMECENTER", "Av. La Marina 2500", "999-777-888", "corp@promart.pe"),
    ("10456789011", "JUAN PEREZ (TRANSPORTISTA)", "Urb. Los Ficus", "999-999-000", "juan@transporte.pe"),
    ("20333444555", "MAESTRO PERU", "Av. Angamos 1200", "999-101-102", "ventas@maestro.com.pe"),
    ("20777888999", "DISTRIBUIDORA NORTE PACASMAYO", "Av. Argentina 3200", "999-203-204", "ventas@pacasmayo.com.pe")
]

CATEGORIAS_SEED = [
    (1, "Materiales de Construcción"),
    (2, "Acabados y Pintura"),
    (3, "Herramientas Manuales"),
    (4, "EPP / Seguridad"),
    (5, "Oficina y Útiles"),
    (6, "Electricidad"),
    (7, "Gasfitería")
]

# SKU, Nombre, UM, CatID, CostoBase(Neto), PrecioVenta(Neto)
PRODUCTOS_SEED = [
    ("CEMENTO-SOL", "CEMENTO SOL TIPO I", "BOLSA", 1, 24.50, 32.00),
    ("LADRILLO-KK", "LADRILLO KING KONG 18 HUECOS", "MILLAR", 1, 750.00, 1100.00),
    ("FIERRO-1/2", "VARILLA FIERRO CORRUGADO 1/2", "UND", 1, 30.00, 42.00),
    ("ARENA-GRUESA", "ARENA GRUESA (M3)", "M3", 1, 45.00, 65.00),
    
    ("PINT-VENC-BL", "PINTURA LATEX VENCEDOR BLANCO", "LATE", 2, 40.00, 65.00),
    ("THINNER-ACR", "THINNER ACRILICO", "GALON", 2, 15.00, 25.00),
    ("BROCHA-4", "BROCHA CERDA FINA 4 PULG", "UND", 2, 8.00, 15.00),
    
    ("ALICATE-UNIV", "ALICATE UNIVERSAL 8 PULG", "UND", 3, 22.00, 35.00),
    ("MARTILLO-CARP", "MARTILLO CARPINTERO STANLEY", "UND", 3, 35.00, 55.00),
    ("DEST-PHILIPS", "DESTORNILLADOR PHILIPS 6X100", "UND", 3, 6.50, 12.00),
    
    ("CASCO-SEG-AM", "CASCO SEGURIDAD AMARILLO", "UND", 4, 10.00, 18.00),
    ("GUANTE-CUERO", "GUANTES DE CUERO REFORZADO", "PAR", 4, 7.50, 15.00),
    ("LENTES-PROT", "LENTES SEGURIDAD TRANSPARENTE", "UND", 4, 5.00, 12.00),
    
    ("PAPEL-BOND", "PAPEL BOND A4 75GR", "PAQUETE", 5, 12.00, 18.00),
    
    ("CABLE-12AWG", "CABLE ELECTRICO 12AWG (ROLLO 100M)", "ROLLO", 6, 120.00, 180.00),
    ("INTERRUPTOR-D", "INTERRUPTOR DOBLE EMPOTRABLE", "UND", 6, 8.50, 15.00),
    
    ("TUBO-PVC-1/2", "TUBO PVC AGUA 1/2 PULG", "UND", 7, 6.00, 10.00),
    ("CODO-PVC-1/2", "CODO PVC 90 AGUA 1/2 PULG", "UND", 7, 1.50, 3.00)
]

def generate_db():
    print(f"📡 Conectando a {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Limpieza
    setup_tables(cursor)

    # 2. Insert Maestros
    insert_maestros(cursor)

    # 3. Simulación de Compras (Día a día para mantener lógica de Stock/Costo)
    # Primero insertamos productos con Stock 0 y Costo 0
    # Map SKU -> ID
    sku_to_id = {}
    for prod in PRODUCTOS_SEED:
        cursor.execute("""
            INSERT INTO productos (codigo_sku, nombre, unidad_medida, categoria_id, stock_actual, costo_promedio, precio_venta)
            VALUES (?, ?, ?, ?, 0, 0, ?)
        """, (prod[0], prod[1], prod[2], prod[3], prod[5]))
        sku_to_id[prod[0]] = cursor.lastrowid
        # Inicializar localmente para tracking
        prod_state[prod[0]] = {"stock": 0.0, "costo": 0.0, "base_cost": prod[4]}

    today = date.today()
    start_date = today - timedelta(days=DAYS_HISTORY)
    
    # Provider IDs
    cursor.execute("SELECT id FROM proveedores")
    prov_ids = [r[0] for r in cursor.fetchall()]

    print(f"⏳ Simulando {DAYS_HISTORY} días de operaciones...")

    total_compras = 0
    
    for i in range(DAYS_HISTORY + 1):
        current_date = start_date + timedelta(days=i)
        
        # Chance de tener compra hoy
        if random.random() < PERCENT_PURCHASE_CHANCE_DAILY:
            # Cuántas facturas hoy? 1 o 2
            num_facturas = random.randint(1, 2)
            
            for _ in range(num_facturas):
                # DATOS CABECERA
                prov_id = random.choice(prov_ids)
                serie = f"F{random.randint(1, 9)}0{random.randint(1, 5)}"
                numero = f"{random.randint(1, 5000):06d}"
                
                moneda = "PEN" if random.random() > 0.2 else "USD"
                
                # Simular T.C. con caminata aleatoria simple
                tc = max(3.50, min(4.10, random.gauss(TC_MEAN, TC_STD)))
                
                # Seleccionar items (1 a 5 productos aleatorios)
                num_items = random.randint(1, 5)
                items_compra = random.sample(PRODUCTOS_SEED, num_items)
                
                detalles = []
                total_neto = 0.0
                total_igv = 0.0
                
                for item in items_compra:
                    sku = item[0]
                    pid = sku_to_id[sku]
                    
                    # Variación de precio base (+- 15%)
                    base_cost = prod_state[sku]["base_cost"]
                    # Inflación leve con el tiempo
                    time_factor = 1 + (i / DAYS_HISTORY * 0.10) 
                    variance = random.uniform(0.85, 1.15)
                    
                    costo_unit_neto_pen = base_cost * time_factor * variance
                    
                    # Convertir a moneda de compra
                    if moneda == "USD":
                        precio_unit_neto_compra = costo_unit_neto_pen / tc
                    else:
                        precio_unit_neto_compra = costo_unit_neto_pen
                        
                    qty = random.randint(5, 50)
                    if item[2] == "MILLAR": qty = random.uniform(0.5, 5.0)
                    
                    # Decisión IGV (Mayoría SI)
                    aplica_igv = True # Simplificación: 100% aplica IGV para evitar líos
                    tax_rate = IGV_RATE
                    
                    precio_unit_total_compra = precio_unit_neto_compra * (1 + tax_rate/100)
                    subtotal = precio_unit_total_compra * qty
                    
                    # Calcular montos para cabecera
                    val_unit_neto_compra = precio_unit_neto_compra
                    igv_unit_compra = val_unit_neto_compra * (tax_rate/100)
                    
                    total_neto += val_unit_neto_compra * qty
                    total_igv += igv_unit_compra * qty
                    
                    # TRACKING STOCK/COSTO (Siempre en PEN para BD)
                    state = prod_state[sku]
                    old_stock = state["stock"]
                    old_cost = state["costo"]
                    
                    # Costo Total en PEN para Ponderado
                    precio_total_pen = precio_unit_total_compra * (tc if moneda == "USD" else 1.0)
                    
                    new_stock = old_stock + qty
                    if new_stock > 0:
                        new_cost = ((old_stock * old_cost) + (qty * precio_total_pen)) / new_stock
                    else:
                        new_cost = precio_total_pen
                        
                    # Actualizar estado
                    state["stock"] = new_stock
                    state["costo"] = new_cost
                    
                    detalles.append({
                        "pid": pid,
                        "desc": item[1],
                        "um": item[2],
                        "qty": qty,
                        "precio_unit": round(precio_unit_total_compra, 4), # Guardamos Total
                        "subtotal": round(subtotal, 4),
                        "costo_previo": round(old_cost, 4), # Costo Promedio ANTES de compra (en PEN siempre?)
                                                            # Ojo: costo_previo se guarda en PEN en tablas? Reviso backend.py:
                                                            # "costo_previo" se saca de `productos.costo_promedio` (PEN). Correcto.
                        "tax": tax_rate
                    })

                total_compra = total_neto + total_igv
                
                # INSERT CABECERA
                cursor.execute("""
                    INSERT INTO compras_cabecera (proveedor_id, fecha_emision, tipo_documento, serie, numero, moneda, tipo_cambio, total_gravada, total_igv, total_compra)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (prov_id, current_date, "FACTURA", serie, numero, moneda, round(tc, 3), round(total_neto, 2), round(total_igv, 2), round(total_compra, 2)))
                compra_id = cursor.lastrowid
                
                # INSERT DETALLES y UPDATE PRODUCTOS
                for d in detalles:
                    cursor.execute("""
                        INSERT INTO compras_detalle (compra_id, producto_id, descripcion, unidad_medida, cantidad, precio_unitario, subtotal, costo_previo, tasa_impuesto)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (compra_id, d["pid"], d["desc"], d["um"], d["qty"], d["precio_unit"], d["subtotal"], d["costo_previo"], d["tax"]))
                    
                    # Update Real en BD
                    cursor.execute("""
                        UPDATE productos SET stock_actual = ?, costo_promedio = ? WHERE id = ?
                    """, (prod_state[list(sku_to_id.keys())[list(sku_to_id.values()).index(d["pid"])]]["stock"], 
                          prod_state[list(sku_to_id.keys())[list(sku_to_id.values()).index(d["pid"])]]["costo"], 
                          d["pid"]))

                total_compras += 1

    conn.commit()
    conn.close()
    print(f"✅ Seeding completado. {total_compras} Compras generadas.")

# Global state tracker
prod_state = {}

def setup_tables(cursor):
    tables = ["compras_detalle", "compras_cabecera", "productos", "proveedores", "categorias"]
    for t in tables:
        cursor.execute(f"DELETE FROM {t}")
        cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{t}'")

def insert_maestros(cursor):
    cursor.executemany("INSERT INTO categorias (id, nombre) VALUES (?, ?)", CATEGORIAS_SEED)
    cursor.executemany("INSERT INTO proveedores (ruc_dni, razon_social, direccion, telefono, email) VALUES (?, ?, ?, ?, ?)", PROVEEDORES_SEED)

if __name__ == "__main__":
    generate_db()
