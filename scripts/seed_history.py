import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gestion_basica.db")

def seed_history():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        print("🌱 Generando Historial de Compras (Seed)...")
        
        # Obtener IDs
        cursor.execute("SELECT id FROM proveedores")
        prov_ids = [r[0] for r in cursor.fetchall()]
        
        cursor.execute("SELECT id, precio_venta FROM productos")
        prods = cursor.fetchall() # list of (id, price)
        
        if not prov_ids or not prods:
            print("❌ Faltan proveedores o productos base.")
            return

        # Generar 30 facturas en los últimos 60 días
        for i in range(30):
            # Info Cabecera aleatoria
            prov_id = random.choice(prov_ids)
            dias_atras = random.randint(0, 60)
            fecha = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
            serie = f"F{random.randint(1, 5):03d}"
            numero = f"{random.randint(1, 9999):04d}"
            
            # Info Detalle (1 a 5 items)
            num_items = random.randint(1, 5)
            total_fact = 0
            detalles = []
            
            for _ in range(num_items):
                prod_id, base_price = random.choice(prods)
                qty = random.randint(1, 50)
                # Variar precio +/- 10%
                price = base_price * random.uniform(0.9, 1.1)
                subtotal = qty * price
                total_fact += subtotal
                
                detalles.append((prod_id, qty, price, subtotal))
            
            # Guardar Cab
            cursor.execute("""
                INSERT INTO compras_cabecera (proveedor_id, fecha_emision, tipo_documento, serie, numero, moneda, total_compra, total_gravada, total_igv)
                VALUES (?, ?, 'FACTURA', ?, ?, 'PEN', ?, ?, ?)
            """, (prov_id, fecha, serie, numero, total_fact, total_fact/1.18, total_fact - (total_fact/1.18)))
            
            compra_id = cursor.lastrowid
            
            # Guardar Detalle (Sin actualizar stock/costo complejo aquí para no demorar, solo data visual)
            # Pero para que el dashboard se vea bien, actualizamos stock simple
            for (pid, q, p, sub) in detalles:
                 cursor.execute("""
                    INSERT INTO compras_detalle (compra_id, producto_id, descripcion, unidad_medida, cantidad, precio_unitario, subtotal, costo_previo)
                    VALUES (?, ?, 'Seed Data', 'UND', ?, ?, ?, ?)
                """, (compra_id, pid, q, p, sub, p * 0.95)) # Simular costo previo menor
                 
                 cursor.execute("UPDATE productos SET stock_actual = stock_actual + ? WHERE id = ?", (q, pid))

        conn.commit()
        print("✅ Historial generado con éxito.")
        
    except Exception as e:
        print(f"Error seeding: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed_history()
