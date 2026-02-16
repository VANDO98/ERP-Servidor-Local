
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from src.auth.security import get_current_user
from src.dashboard import service as dash_service
from src.inventory import service as inv_service # Reuse stock logic
# Note: Circular dependency risk if importing service? 
# Router importing service is standard. 
# Dash service importing Inventory service is what I did in dash_service.py. That's fine as long as Inventory doesn't import Dash.

router = APIRouter(prefix="/api", tags=["Dashboard"])

@router.get("/kpis")
def get_kpis(start_date: str = None, end_date: str = None, current_user: dict = Depends(get_current_user)):
    try:
        # Default dates if not provided?
        if not start_date or not end_date:
            # Fallback to current month or similar inside service?
            # Service expects arguments. Let's set defaults here if needed or let service handle.
            # dash_service.obtener_kpis_dashboard uses strict SQL, so None might fail.
            today = datetime.now()
            start_date = today.replace(day=1).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            
        return dash_service.obtener_kpis_dashboard(start_date, end_date)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/complete")
def get_dashboard_complete(start_date: str, end_date: str, current_user: dict = Depends(get_current_user)):
    try:
        data = {
            "kpis": dash_service.obtener_kpis_dashboard(start_date, end_date),
            "top_providers": dash_service.obtener_top_proveedores(start_date, end_date).fillna("").to_dict(orient="records"),
            "categories": dash_service.obtener_gastos_por_categoria(start_date, end_date).fillna("").to_dict(orient="records"),
            "evolution": dash_service.obtener_evolucion_compras(start_date, end_date).fillna("").to_dict(orient="records"),
            "stock_critico": inv_service.obtener_stock_critico().fillna("").to_dict(orient="records"),
            "rotacion": inv_service.obtener_rotacion_inventario().fillna("").to_dict(orient="records"),
            "alertas": dash_service.obtener_alertas_criticas()
        }
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tipo-cambio")
def get_tipo_cambio(current_user: dict = Depends(get_current_user)):
    try:
        from src.shared.external_api import obtener_tc_sunat
        tc = obtener_tc_sunat()
        return {"venta": tc, "compra": tc - 0.01}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
