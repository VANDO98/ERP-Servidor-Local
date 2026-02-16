import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def get_token():
    try:
        r = requests.post(f"{BASE_URL}/token", data={"username": "admin", "password": "admin"})
        if r.status_code == 200:
            return r.json().get("access_token")
        
        # Try fallback
        r = requests.post(f"{BASE_URL}/token", data={"username": "admin", "password": "admin123"})
        if r.status_code == 200:
            return r.json().get("access_token")
    except:
        pass
    return None

def inspect_endpoint(name, url, token):
    print(f"\n--- {name} ({url}) ---")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            print(f"❌ Error {r.status_code}: {r.text}")
            return
        
        data = r.json()
        
        # Handle different response types
        sample = None
        count = 0
        
        if isinstance(data, list):
            count = len(data)
            if count > 0: sample = data[0]
            
        elif isinstance(data, dict):
            # Dashboard returns dict with keys
            if 'kpis' in data:
                print("KEYS:", data.keys())
                # Inspect specific sub-lists
                for key in ['stock_critico', 'top_providers', 'alertas']:
                    if key in data:
                        val = data[key]
                        if isinstance(val, list) and len(val) > 0:
                            print(f"Sample {key}[0]:", json.dumps(val[0], indent=2))
                        elif isinstance(val, dict): # Alertas
                             print(f"Sample {key}: {json.dumps(val, indent=2)}")
                return
            else:
                sample = data
        
        print(f"Count: {count}")
        if sample:
            print("Sample Item:", json.dumps(sample, indent=2))
        else:
            print("Response is empty.")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    with open("data_mapping_log.txt", "w", encoding="utf-8") as f:
        sys.stdout = f
        
        print("Obtaining Token...")
        token = get_token()
        if not token:
            print("❌ Start backend server first or check credentials")
            sys.exit(1)
            
        print("✅ Token obtained")
        
        # 1. Dashboard
        inspect_endpoint("DASHBOARD", f"{BASE_URL}/dashboard/complete?start_date=2024-01-01&end_date=2025-12-31", token)
        
        # 2. Inventory (Products)
        inspect_endpoint("PRODUCTS", f"{BASE_URL}/products", token)
        
        # 3. Inventory (Detailed)
        inspect_endpoint("INV DETAILED", f"{BASE_URL}/inventory/detailed", token)
        
        # 4. OC (Orders)
        inspect_endpoint("ORDERS", f"{BASE_URL}/orders", token)
        
        # 5. Guides
        inspect_endpoint("GUIDES", f"{BASE_URL}/guides", token)
        
        # 6. Purchases Detailed
        inspect_endpoint("PURCHASES DETAILED", f"{BASE_URL}/purchases/detailed", token)
        
        sys.stdout = sys.__stdout__
    print("Check data_mapping_log.txt")
