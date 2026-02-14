import sqlite3
import os

# Ruta a la BD
DB_NAME = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gestion_basica.db")

def reset_and_seed():
    if not os.path.exists(DB_NAME):
        print(f"Error: No se encuentra la BD en {DB_NAME}")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        print("🚨 INICIANDO REINICIO DE BASE DE DATOS...")
        
        # 1. Limpiar tablas (Orden importa por FKs)
        tables = ["compras_detalle", "compras_cabecera", "productos", "proveedores", "categorias"]
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'") # Reiniciar IDs
            print(f"- Tabla '{table}' vaciada.")
            
        print("✅ Datos eliminados. Iniciando carga de datos de prueba...")

        # 2. Insertar CATEGORIAS
        categorias = [
            (1, "Materiales de Construcción"),
            (2, "Acabados y Pintura"),
            (3, "Herramientas Manuales"),
            (4, "EPP / Seguridad"),
            (5, "Oficina y Útiles")
        ]
        cursor.executemany("INSERT INTO categorias (id, nombre) VALUES (?, ?)", categorias)
        print(f"- {len(categorias)} Categorías insertadas.")

        # 3. Insertar PROVEEDORES
        proveedores = [
            ("20100055511", "ACEROS AREQUIPA S.A.", "Av. Enrique Meiggs 297, Callao"),
            ("20503840123", "SODIMAC PERU S.A.", "Av. Javier Prado Este 1059, La Victoria"),
            ("20600012345", "FERRETERIA EL TORNILLO SAC", "Jr. Puno 123, Cercado"),
            ("20456789012", "PROMART HOMECENTER", "Av. La Marina 2500, San Miguel"),
            ("10456789011", "JUAN PEREZ (TRANSPORTISTA)", "Urb. Los Ficus Mz A Lt 5")
        ]
        # Schema: ruc_dni, razon_social, direccion, telefono, email
        cursor.executemany("""
            INSERT INTO proveedores (ruc_dni, razon_social, direccion, telefono, email) 
            VALUES (?, ?, ?, '999-000-000', 'contacto@ejemplo.com')
        """, proveedores)
        print(f"- {len(proveedores)} Proveedores insertados.")

        # 4. Insertar PRODUCTOS
        # Schema: codigo_sku, nombre, unidad_medida, categoria_id, costo, precio
        productos = [
            # Constr.
            ("CEMENTO-SOL", "CEMENTO SOL TIPO I", "BOLSA", 1, 28.50, 32.00),
            ("LADRILLO-KK", "LADRILLO KING KONG 18 HUECOS", "MILLAR", 1, 850.00, 1100.00),
            ("FIERRO-1/2", "VARILLA FIERRO CORRUGADO 1/2", "UND", 1, 35.00, 42.00),
            # Acabados
            ("PINT-VENC-BL", "PINTURA LATEX VENCEDOR BLANCO", "LATE", 2, 45.00, 65.00),
            ("THINNER-ACR", "THINNER ACRILICO", "GALON", 2, 18.00, 25.00),
            # Herramientas
            ("ALICATE-UNIV", "ALICATE UNIVERSAL 8 PULG", "UND", 3, 25.00, 35.00),
            ("MARTILLO-CARP", "MARTILLO CARPINTERO STANLEY", "UND", 3, 40.00, 55.00),
            # EPP
            ("CASCO-SEG-AM", "CASCO SEGURIDAD AMARILLO", "UND", 4, 12.00, 18.00),
            ("GUANTE-CUERO", "GUANTES DE CUERO REFORZADO", "PAR", 4, 8.50, 15.00),
            # Oficina
            ("PAPEL-BOND", "PAPEL BOND A4 75GR", "PAQUETE", 5, 14.50, 18.00)
        ]
        
        cursor.executemany("""
            INSERT INTO productos (codigo_sku, nombre, unidad_medida, categoria_id, costo_promedio, precio_venta) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, productos)
        print(f"- {len(productos)} Productos insertados.")

        conn.commit()
        print("🚀 BASE DE DATOS REINICIADA Y POBLADA CON ÉXITO.")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error durante el proceso: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_and_seed()
