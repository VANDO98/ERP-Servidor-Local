
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from src.auth.security import get_current_user
from src.inventory import service as inv_service

router = APIRouter(prefix="/api", tags=["Inventory"])

# --- Models ---
class ProductCreate(BaseModel):
    nombre: str
    codigo_sku: Optional[str] = None
    categoria_id: Optional[int] = None
    precio_venta: Optional[float] = 0.0
    costo_promedio: Optional[float] = 0.0
    stock_minimo: Optional[float] = 5.0
    unidad_medida: Optional[str] = 'UN'
    subcategoria: Optional[str] = ""

class WarehouseCreate(BaseModel):
    nombre: str
    ubicacion: Optional[str] = ""

class CategoryCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = ""

class MovementItem(BaseModel):
    pid: int
    cantidad: float
    almacen_id: Optional[int] = 1

class MovementRequest(BaseModel):
    type: str # 'SALIDA' or 'TRASLADO'
    fecha: str
    observaciones: str
    # Salida specific
    tipo_salida: Optional[str] = None
    destino: Optional[str] = None
    # Traslado specific
    origen_id: Optional[int] = None
    destino_id: Optional[int] = None
    items: List[MovementItem]

# --- Endpoints ---

@router.get("/products")
def get_products(current_user: dict = Depends(get_current_user)):
    """Retorna lista extendida de productos con stock global"""
    try:
        df = inv_service.obtener_productos_extendido()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/products")
def create_product(product: ProductCreate, current_user: dict = Depends(get_current_user)):
    try:
        ok, msg = inv_service.crear_producto(product.dict())
        if ok:
            return {"status": "success", "msg": msg}
        else:
            raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/warehouses")
def get_warehouses(current_user: dict = Depends(get_current_user)):
    try:
        df = inv_service.obtener_almacenes()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/warehouses")
def create_warehouse(warehouse: WarehouseCreate, current_user: dict = Depends(get_current_user)):
    try:
        ok, msg = inv_service.crear_almacen(warehouse.nombre, warehouse.ubicacion)
        if ok:
            return {"status": "success", "msg": msg}
        else:
            raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
def get_categories(current_user: dict = Depends(get_current_user)):
    try:
        df = inv_service.obtener_categorias()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/categories")
def create_category(category: CategoryCreate, current_user: dict = Depends(get_current_user)):
    try:
        ok, msg = inv_service.crear_categoria(category.nombre, category.descripcion)
        if ok:
            return {"status": "success", "msg": msg}
        else:
            raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/detailed")
def get_inventory_detailed(current_user: dict = Depends(get_current_user)):
    """Retorna inventario desglosado por almacén"""
    try:
        df = inv_service.obtener_inventario_detallado()
        return df.fillna(0).to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/fifo")
def get_inventory_fifo(include_igv: bool = True, current_user: dict = Depends(get_current_user)):
    try:
        total, map_fifo = inv_service.calcular_valorizado_fifo(incluir_igv=include_igv)
        # Extend with product info
        df = inv_service.obtener_productos_extendido()
        
        result = []
        if not df.empty:
            for _, row in df.iterrows():
                pid = row['id']
                val_data = map_fifo.get(pid, {'valor': 0.0})
                # Determinar estado
                stock = row['stock_actual']
                min_stock = row['stock_minimo']
                if stock <= 0:
                    estado = "Sin Stock"
                elif min_stock > 0 and stock <= min_stock * 0.5:
                    estado = "Crítico"
                elif min_stock > 0 and stock <= min_stock:
                    estado = "Bajo"
                else:
                    estado = "Normal"

                result.append({
                    "id": pid,
                    "sku": row['codigo_sku'],
                    "producto": row['nombre'],
                    "categoria": row['categoria_nombre'],
                    "unidad": row['unidad_medida'],
                    "stock": stock,
                    "fifo_valuated": val_data['valor'],
                    "costo_unitario": val_data['valor'] / stock if stock > 0 else row['costo_promedio'],
                    "valor_total": val_data['valor'],
                    "estado": estado
                })
        return {"total_valuation": total, "items": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/movements")
def register_movement(req: MovementRequest, current_user: dict = Depends(get_current_user)):
    try:
        detalles = [i.dict() for i in req.items]
        
        if req.type == 'SALIDA':
            cab = {
                "fecha": req.fecha,
                "tipo": req.tipo_salida,
                "destino": req.destino,
                "obs": req.observaciones
            }
            # Adapt items keys to service expectation ('pid', 'cantidad', 'almacen_id') - already in dict
            
            ok, msg = inv_service.registrar_salida(cab, detalles)
            if ok: return {"status": "success", "msg": msg}
            else: raise HTTPException(status_code=400, detail=msg)
            
        elif req.type == 'TRASLADO':
            cab = {
                "fecha": req.fecha,
                "origen_id": req.origen_id,
                "destino_id": req.destino_id,
                "observaciones": req.observaciones
            }
            
            ok, msg = inv_service.registrar_traslado(cab, detalles)
            if ok: return {"status": "success", "msg": msg}
            else: raise HTTPException(status_code=400, detail=msg)
                  
        else:
            raise HTTPException(status_code=400, detail="Invalid movement type")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/kardex/general")
def get_kardex_general(start_date: str, end_date: str, current_user: dict = Depends(get_current_user)):
    """General Kardex with all movements"""
    try:
        df = inv_service.obtener_kardex_general(start_date, end_date)
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

@router.get("/inventory/kardex/{product_id}")
def get_kardex(product_id: int, start_date: str = None, end_date: str = None, current_user: dict = Depends(get_current_user)):
    try:
        df = inv_service.obtener_kardex_producto(product_id, start_date, end_date)
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
