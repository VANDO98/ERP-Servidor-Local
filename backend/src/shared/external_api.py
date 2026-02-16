
import requests
import urllib3

# Disable insecure request warnings (if necessary for specific legacy APIs, though requests standard usually verifies)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import time

# Cache simple: { 'valor': 3.75, 'timestamp': 123456789 }
_tc_cache = {'valor': None, 'timestamp': 0}
CACHE_DURATION = 3600 # 1 hour

def obtener_tc_sunat():
    """
    Obtiene T.C. Venta de SUNAT (API externa).
    Retorna float. En caso de error retorna 3.75 como fallback.
    """
    global _tc_cache
    
    # Check cache
    if _tc_cache['valor'] and (time.time() - _tc_cache['timestamp'] < CACHE_DURATION):
        return _tc_cache['valor']

    url = "https://api.apis.net.pe/v1/tipo-cambio-sunat"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            tc = float(data['venta'])
            # Update cache
            _tc_cache = {'valor': tc, 'timestamp': time.time()}
            return tc
        return 3.75
    except Exception as e:
        print(f"Error obteniendo TC: {e}")
        return 3.75
