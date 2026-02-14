import sqlite3
import os
import datetime

DB_NAME = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "gestion_basica.db")
# El HTML se guarda en /docs
HTML_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "manual_tecnico_bd.html")

def get_mermaid_schema():
    if not os.path.exists(DB_NAME):
        return "graph TD; A[Error: No existe la BD] --> B[Ejecuta primero app.py]"
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    mermaid = "erDiagram\n"
    
    try:
        # 1. Obtener Tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
        tablas = cursor.fetchall()
        
        # 2. Definir Entidades
        for (table_name,) in tablas:
            mermaid += f"    {table_name.upper()} {{\n"
            
            # Columnas
            cursor.execute(f"PRAGMA table_info({table_name})")
            cols = cursor.fetchall()
            for col in cols:
                # cid(0), name(1), type(2), notnull(3), dflt_value(4), pk(5)
                nombre = col[1]
                tipo = col[2] if col[2] else "TEXT"
                pk_str = "PK" if col[5] else ""
                fk_comment = "" 
                if "_id" in nombre: fk_comment = "FK"
                
                mermaid += f"        {tipo} {nombre} {pk_str} {fk_comment}\n"
            
            mermaid += "    }\n"

        # 3. Definir Relaciones (Foreign Keys)
        for (table_name,) in tablas:
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            fks = cursor.fetchall()
            # id, seq, table(2), from(3), to(4), on_update, on_delete, match
            for fk in fks:
                tabla_destino = fk[2]
                mermaid += f"    {tabla_destino.upper()} ||--o{{ {table_name.upper()} : contiene\n"
                
    except Exception as e:
        print(f"Error leyendo esquema: {e}")
        mermaid += f"    ERROR {{ string mensaje \"{str(e)}\" }}"
        
    finally:
        conn.close()
        
    return mermaid

def generar_html_integrado():
    mermaid_code = get_mermaid_schema()
    fecha_act = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manual Técnico - Base de Datos ERP Lite</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true }});
    </script>
    <style>
        :root {{
            --primary-color: #2563eb;
            --text-color: #374151;
            --bg-color: #f3f4f6;
            --card-bg: #ffffff;
        }}
        body {{
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--bg-color);
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background-color: var(--card-bg);
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }}
        h1 {{
            color: #1e3a8a;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: var(--primary-color);
            margin-top: 40px;
            font-size: 1.5em;
            border-left: 4px solid var(--primary-color);
            padding-left: 10px;
        }}
        h3 {{
            color: #4b5563;
            margin-top: 20px;
            font-size: 1.2em;
        }}
        .concept-card {{
            background-color: #eff6ff;
            border: 1px solid #bfdbfe;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 6px;
        }}
        .concept-title {{
            font-weight: bold;
            color: #1e40af;
            display: block;
            margin-bottom: 5px;
        }}
        code {{
            background-color: #f1f5f9;
            padding: 2px 5px;
            border-radius: 4px;
            font-family: Consolas, Monaco, 'Andale Mono', monospace;
            color: #ef4444;
        }}
        .diagram-container {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
            overflow-x: auto;
            display: flex;
            justify-content: center;
        }}
        .practical-example {{
            background-color: #ecfdf5;
            border: 1px solid #d1fae5;
            padding: 20px;
            border-radius: 8px;
        }}
        .timestamp {{
            text-align: right;
            font-size: 0.8em;
            color: #9ca3af;
            margin-bottom: 20px;
        }}
        .footer {{
            margin-top: 40px;
            text-align: center;
            font-size: 0.9em;
            color: #9ca3af;
            border-top: 1px solid #e5e7eb;
            padding-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="timestamp">Última actualización del esquema: {fecha_act}</div>
        <h1>📔 Manual Técnico de la Base de Datos</h1>

        <h2>1. Conceptos Fundamentales (Claves)</h2>
        <p>Para que la base de datos "hable" y conecte la información, usamos dos tipos de claves:</p>

        <div class="concept-card">
            <span class="concept-title">🔑 PK (Primary Key / Llave Primaria)</span>
            <ul>
                <li><strong>¿Qué es?</strong>: Es el DNI de cada registro. Un número único que identifica irrepetiblemente a una fila.</li>
                <li><strong>Ejemplo</strong>: En la tabla <code>productos</code>, el <code>id=5</code> es ÚNICO para el "Martillo". No puede haber otro producto con <code>id=5</code>.</li>
            </ul>
        </div>

        <div class="concept-card">
            <span class="concept-title">🔗 FK (Foreign Key / Llave Foránea)</span>
            <ul>
                <li><strong>¿Qué es?</strong>: Es un "puntero" o "ancla" que conecta una tabla con otra. En lugar de escribir toda la información de nuevo, guardamos solo el ID de referencia.</li>
                <li><strong>Ejemplo</strong>: En la factura, no escribimos "Proveedor: Ferretería Central...". Solo guardamos <code>proveedor_id = 8</code>. La base de datos busca el ID 8 en la tabla proveedores y recupera toda la info.</li>
            </ul>
        </div>

        <h2>2. Explicación de las Relaciones</h2>
        <p>El diagrama muestra cómo fluye la información. Vamos de lo general a lo específico:</p>

        <h3>A. Proveedores y Compras</h3>
        <ul>
            <li><strong>Relación</strong>: Uno a Muchos (1:N).</li>
            <li><strong>Lectura</strong>: <em>"Un Proveedor puede tener MUCHAS Facturas de compra, pero una Factura pertenece a UN solo proveedor".</em></li>
        </ul>

        <h3>B. Compras y Detalles</h3>
        <ul>
            <li><strong>Relación</strong>: Uno a Muchos (1:N).</li>
            <li><strong>Lectura</strong>: <em>"Una Factura (Cabecera) se compone de MUCHAS líneas de detalle (ítems), pero una línea de detalle pertenece a UNA única factura".</em></li>
        </ul>

        <h2>3. Diagrama Visual en Vivo</h2>
        <p>Este gráfico se genera automáticamente leyendo la estructura real de tu archivo <code>{DB_NAME}</code>.</p>
        
        <div class="diagram-container">
            <div class="mermaid">
{mermaid_code}
            </div>
        </div>
        <p style="text-align: center; font-size: 0.9em; color: #666;">
            <em>Para actualizar este gráfico tras cambios en la BD, ejecuta: <code>python generar_diagrama.py</code></em>
        </p>

        <div class="footer">
            Sistema ERP Lite - Documentación Dinámica
        </div>
    </div>
</body>
</html>"""

    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ Manual Integrado generado en: {os.path.abspath(HTML_FILE)}")

if __name__ == "__main__":
    generar_html_integrado()
