
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from datetime import date

from src.auth.security import get_current_user
from src.logistics import service

router = APIRouter(prefix="/api", tags=["Logistics"])

# Schemas
class GuiaItem(BaseModel):
    pid: int
    cantidad: float
    almacen_id: int = 1

class GuiaCreate(BaseModel):
    proveedor_id: int
    oc_id: Optional[int] = None
    numero_guia: str
    fecha_recepcion: str # YYYY-MM-DD
    items: List[GuiaItem]

# Endpoints
@router.get("/guides")
def get_guides(current_user: dict = Depends(get_current_user)):
    try:
        df = service.listar_guias()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/guides/{gid}")
def get_guide_detail(gid: int, current_user: dict = Depends(get_current_user)):
    data = service.obtener_guia(gid)
    if not data:
        raise HTTPException(status_code=404, detail="Guía no encontrada")
    return data

@router.post("/guides")
def create_guide(guia: GuiaCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] not in ['admin', 'user']:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    ok, msg = service.crear_guia_remision(guia.dict())
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "msg": msg}
