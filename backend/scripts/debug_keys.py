
import requests
import json
import sqlite3

BASE_URL = "http://localhost:8000/api"

def get_token():
    try:
        resp = requests.post(f"{BASE_URL}/token", data={"username": "tester", "password": "123"})
        if resp.status_code == 200:
            return resp.json()["access_token"]
        print(f"Login failed: {resp.text}")
        return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def debug_keys():
    token = get_token()
    if not token: return

    headers = {"Authorization": f"Bearer {token}"}

    print("\n--- ORDERS KEYS ---")
    try:
        resp = requests.get(f"{BASE_URL}/orders", headers=headers)
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            print("First Order Keys:", list(data[0].keys()))
            print("First Order ID value:", data[0].get('id'), "Type:", type(data[0].get('id')))
        else:
            print("Orders response:", data)
    except Exception as e:
        print(f"Orders Error: {e}")

    print("\n--- DASHBOARD DATA ---")
    try:
        resp = requests.get(f"{BASE_URL}/dashboard/complete?start_date=2024-01-01&end_date=2026-12-31", headers=headers)
        data = resp.json()
        print("Dashboard Root Keys:", list(data.keys()))
        if 'kpis' in data:
            print("KPIs Keys:", list(data['kpis'].keys()))
    except Exception as e:
        print(f"Dashboard Error: {e}")

if __name__ == "__main__":
    debug_keys()
