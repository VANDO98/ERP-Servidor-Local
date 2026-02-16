
import time
import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from src.dashboard import service as dash_service

def profile():
    print("--- Starting Dashboard Profiling ---")
    
    start_time = time.time()
    
    # 1. KPIs
    t0 = time.time()
    kpis = dash_service.obtener_kpis_dashboard('2024-01-01', '2025-12-31')
    t1 = time.time()
    print(f"KPIs Time: {t1 - t0:.4f}s")
    
    # 2. Evolution
    t0 = time.time()
    evo = dash_service.obtener_evolucion_compras('2024-01-01', '2025-12-31')
    t1 = time.time()
    print(f"Evolution Time: {t1 - t0:.4f}s")
    
    # 3. Categories
    t0 = time.time()
    cats = dash_service.obtener_gastos_por_categoria('2024-01-01', '2025-12-31')
    t1 = time.time()
    print(f"Categories Time: {t1 - t0:.4f}s")
    
    # 4. Alerts (Suspected Bottleneck)
    t0 = time.time()
    alerts = dash_service.obtener_alertas_criticas()
    t1 = time.time()
    print(f"Alerts Time: {t1 - t0:.4f}s")
    
    total_time = time.time() - start_time
    print(f"--- Total Time: {total_time:.4f}s ---")

if __name__ == "__main__":
    profile()
