import sys
import os
import json

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from main import app
from src.backend import get_connection

client = TestClient(app)

print("--- TESTING API ENDPOINT (FASTAPI SERIALIZATION) ---")

try:
    # 1. Test Endpoint
    print("\n1. Requesting GET /api/orders/pending ...")
    response = client.get("/api/orders/pending")
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   Success! Received {len(data)} records.")
        if data:
            print(f"   First record sample: {data[0]}")
        else:
            print("   Response is empty list []")
    else:
        print(f"   FAILED: {response.text}")

    # 2. Inspect DB Statuses (Case Sensitivity Check)
    print("\n2. Inspecting DB Status Values...")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT estado FROM ordenes_compra")
    statuses = [row[0] for row in cursor.fetchall()]
    print(f"   Found Statuses in DB: {statuses}")
    
    expected = {'APROBADA', 'PENDIENTE', 'FACTURADA'}
    found_normalized = {s.upper() for s in statuses if s}
    
    if not expected.intersection(found_normalized):
        print("   WARNING: No matching statuses found! Query expects: APROBADA, PENDIENTE, FACTURADA")
        
    conn.close()

except Exception as e:
    print(f"CRITICAL ERROR during TestClient execution: {e}")
    import traceback
    traceback.print_exc()
