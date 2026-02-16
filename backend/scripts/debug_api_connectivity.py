import requests
import sys
import json

BASE_URL = "http://localhost:8000"

def run_test():
    print("--- DIAGNOSTICO DE CONECTIVIDAD API ---")
    
    # 1. Test Public Endpoint
    try:
        print(f"\n1. Probando root ({BASE_URL}/)...")
        r = requests.get(f"{BASE_URL}/")
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            print("   ✅ Backend accesible")
        else:
            print("   ❌ Backend respondió con error")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        print("   STOP: El servidor no parece estar corriendo en el puerto 8000.")
        return

    # 2. Test Login (Get Token)
    print("\n2. Probando Autenticacion (/api/auth/token)...")
    token = None
    try:
        # Intenta credenciales por defecto
        chain_creds = [
            ("admin", "admin"),      # Default
            ("admin", "admin123"),   # Common
            ("Admin Test", "admin123")
        ]
        
        for user, pwd in chain_creds:
            print(f"   Intentando login con {user}...")
            r = requests.post(f"{BASE_URL}/api/token", data={
                "username": user,
                "password": pwd
            })
            if r.status_code == 200:
                data = r.json()
                token = data.get("access_token")
                print("   ✅ Login exitoso. Token obtenido.")
                break
            else:
                print(f"   ⚠️ Falló ({r.status_code}): {r.text}")
                
    except Exception as e:
        print(f"   ❌ Error en login: {e}")

    if not token:
        print("   ❌ No se pudo obtener token. No se pueden probar endpoints protegidos.")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Test Dashboard Endpoint
    print("\n3. Probando Endpoint Protegido (Dashboard)...")
    try:
        # Use a wide range date
        url = f"{BASE_URL}/api/dashboard/complete?start_date=2024-01-01&end_date=2025-12-31"
        r = requests.get(url, headers=headers)
        print(f"   URL: {url}")
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            kpis = data.get('kpis', {})
            print(f"   ✅ Datos recibidos. KPIs: {kpis}")
        else:
            print(f"   ❌ Error: {r.text}")
    except Exception as e:
        print(f"   ❌ Error test dashboard: {e}")

    # 4. Test Inventory Endpoint
    print("\n4. Probando Endpoint Inventario (/api/inventory/detailed)...")
    try:
        r = requests.get(f"{BASE_URL}/api/inventory/detailed", headers=headers)
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Inventario recibido. {len(data)} items encontrados.")
        else:
            print(f"   ❌ Error: {r.text}")
    except Exception as e:
        print(f"   ❌ Error test inventario: {e}")

if __name__ == "__main__":
    with open("debug_output.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        run_test()
        sys.stdout = sys.__stdout__
    print("Diagnóstico completado. Ver debug_output.txt")
