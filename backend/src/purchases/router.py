
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from src.auth.security import get_current_user
from src.purchases import service as purch_service

router = APIRouter(prefix="/api", tags=["Purchases"])

# --- Models ---

class ProviderCreate(BaseModel):
    ruc: Optional[str] = None
    razon_social: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None

class OrderItem(BaseModel):
    pid: int
    cantidad: float
    precio_unitario: float
    um: Optional[str] = None

class OrderRequest(BaseModel):
    proveedor_id: int
    fecha: str
    moneda: str
    items: List[OrderItem]
    fecha_entrega: Optional[str] = None
    tasa_igv: Optional[float] = 18.0
    observaciones: Optional[str] = ""

class CompraItem(BaseModel):
    pid: int
    cantidad: float
    precio_unitario: float

class CompraRequest(BaseModel):
    proveedor_id: int
    fecha: str
    moneda: str
    itemsToRegister: List[CompraItem]
    serie: str
    numero: str
    tc: float
    orden_compra_id: Optional[int] = None

# --- Endpoints ---

@router.get("/providers")
def get_providers(current_user: dict = Depends(get_current_user)):
    try:
        df = purch_service.obtener_proveedores()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/providers")
def create_provider(provider: ProviderCreate, current_user: dict = Depends(get_current_user)):
    try:
        ok, msg = purch_service.crear_proveedor(provider.dict())
        if ok:
            return {"status": "success", "msg": msg}
        else:
            raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders")
def get_orders(current_user: dict = Depends(get_current_user)):
    try:
        df = purch_service.obtener_ordenes_compra()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders")
def create_order(order: OrderRequest, current_user: dict = Depends(get_current_user)):
    try:
        items_list = [i.dict() for i in order.items]
        
        orden_id = purch_service.crear_orden_compra_con_correlativo(
            proveedor_id=order.proveedor_id,
            fecha_emision=order.fecha,
            fecha_entrega_estimada=order.fecha_entrega or order.fecha,
            moneda=order.moneda,
            tasa_igv=order.tasa_igv,
            observaciones=order.observaciones,
            items=items_list
        )
        return {
            "success": True, 
            "orden_id": orden_id, 
            "correlativo": f"OC-{str(orden_id).zfill(6)}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders/pending")
def get_pending_orders(current_user: dict = Depends(get_current_user)):
    try:
        df = purch_service.obtener_ordenes_pendientes()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/{oid}")
def get_order(oid: int, current_user: dict = Depends(get_current_user)):
    try:
        data = purch_service.obtener_orden_compra(oid)
        if not data:
            raise HTTPException(status_code=404, detail="Order not found")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{oid}/balance")
def get_order_balance(oid: int, current_user: dict = Depends(get_current_user)):
    try:
        data = purch_service.obtener_saldo_orden(oid)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/orders/{oid}/status")
def update_order_status(oid: int, status: str, current_user: dict = Depends(get_current_user)):
    try:
        ok, msg = purch_service.actualizar_estado_oc(oid, status)
        if ok: return {"status": "success", "msg": msg}
        else: raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/purchases")
def register_purchase(req: CompraRequest, current_user: dict = Depends(get_current_user)):
    try:
        detalles = [i.dict() for i in req.itemsToRegister]
        
        cabecera = {
            'proveedor_id': req.proveedor_id,
            'fecha': req.fecha,
            'moneda': req.moneda,
            'tc': req.tc,
            'serie': req.serie,
            'numero': req.numero,
            'tipo_documento': 'FACTURA',
            'total': sum(i.cantidad * i.precio_unitario for i in req.itemsToRegister),
            'orden_compra_id': req.orden_compra_id
        }

        res = purch_service.registrar_compra(cabecera, detalles)
        
        if res['success']:
            return {"status": "success", "id": res['compra_id']}
        else:
            raise HTTPException(status_code=400, detail=res['error'])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/purchases/summary")
def get_purchases_summary(current_user: dict = Depends(get_current_user)):
    try:
        df = purch_service.obtener_compras_historial()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/purchases/detailed")
def get_purchases_detailed(current_user: dict = Depends(get_current_user)):
    try:
        df = purch_service.obtener_detalle_compras()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
