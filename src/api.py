import requests
import sqlite3
from datetime import datetime, date
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "gestion_basica.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def obtener_tc_sunat(fecha_query=None):
    """
    Obtiene el TC de venta de una API pública.
    Fuente: apis.net.pe (Gratis y estable para T.C.)
    Fallback: valor previo o 3.75
    """
    if fecha_query is None:
        fecha_query = date.today()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Verificar si ya tenemos el TC de hoy en DB
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS tipo_cambio (fecha TEXT PRIMARY KEY, venta REAL, compra REAL, origen TEXT)")
        cursor.execute("SELECT venta FROM tipo_cambio WHERE fecha = ?", (fecha_query.isoformat(),))
        row = cursor.fetchone()
        if row:
            conn.close()
            return row[0]
    except Exception as e:
        print(f"Error DB TC: {e}")

    # 2. Consultar API Externa
    print(f"🌐 Consultando API TC para {fecha_query}...")
    tc_val = 3.75 # Default Fallback
    
    try:
        # API Gratuita de Sunat (no requiere token)
        url = "https://api.apis.net.pe/v1/tipo-cambio-sunat" 
        # Si quisiéramos fecha especifica: ?fecha=YYYY-MM-DD
        
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            tc_venta = data.get('venta')
            tc_compra = data.get('compra')
            
            if tc_venta:
                tc_val = float(tc_venta)
                
                # 3. Guardar en DB
                try:
                    cursor.execute("INSERT OR REPLACE INTO tipo_cambio (fecha, venta, compra, origen) VALUES (?, ?, ?, ?)", 
                                   (fecha_query.isoformat(), tc_val, tc_compra, 'API_SUNAT'))
                    conn.commit()
                except Exception as db_err:
                     print(f"No se pudo guardar TC: {db_err}")
    except Exception as e:
        print(f"⚠️ Error consultando API TC: {e}")
        # Intentar obtener el último conocido
        try:
             cursor.execute("SELECT venta FROM tipo_cambio ORDER BY fecha DESC LIMIT 1")
             last = cursor.fetchone()
             if last: tc_val = last[0]
        except: pass

    conn.close()
    return tc_val
