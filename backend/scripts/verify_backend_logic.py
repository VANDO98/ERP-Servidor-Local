import sys
import os
import json
import pandas as pd
import datetime

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.backend import obtener_ordenes_pendientes

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

print("--- DEEP VALIDATION OF BACKEND LOGIC ---")

try:
    print("1. Calling obtener_ordenes_pendientes()...")
    data = obtener_ordenes_pendientes()
    
    print(f"2. Data retrieved. Type: {type(data)}")
    
    if not data:
        print("WARNING: No data returned (Empty list).")
        # Ensure it returns list, not None
        if data is None:
            print("CRITICAL: Function returned None instead of []")
        sys.exit(0)
        
    print(f"3. Record Count: {len(data)}")
    first_item = data[0]
    print(f"4. First Record Keys: {list(first_item.keys())}")
    print(f"5. First Record Values: {first_item}")
    
    # Validation against Frontend Expectations
    required_fields = ['id', 'proveedor_nombre', 'fecha']
    missing_fields = [f for f in required_fields if f not in first_item]
    
    if missing_fields:
        print(f"CRITICAL ERROR: Missing fields expected by Frontend: {missing_fields}")
    else:
        print("SUCCESS: All required fields ('id', 'proveedor_nombre', 'fecha') are present.")
        
    # JSON Serialization Test
    print("6. Testing JSON Serialization (FastAPI Simulation)...")
    try:
        # FastAPI uses default json encoder usually, but let's see if standard json dumps works
        # or if we have weird numpy types
        json_str = json.dumps(data, default=str) # FastAPI handles datetime, but numpy types can be tricky
        print("JSON Serialization successful.")
    except Exception as e:
        print(f"CRITICAL ERROR: JSON Serialization failed! {e}")
        # Check for numpy types
        for k, v in first_item.items():
            print(f"  - {k}: {type(v)}")

except Exception as e:
    print(f"CRITICAL EXCEPTION during execution: {e}")
    import traceback
    traceback.print_exc()
