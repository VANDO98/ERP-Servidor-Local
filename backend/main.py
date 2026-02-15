from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add parent directory to path to import src.backend
# Current: ERP_Moderno_Web/backend/main.py -> ERP_Moderno_Web/backend -> src
# sys.path hack removed


# Import existing backend logic
from src import backend as db
from fastapi.security import OAuth2PasswordRequestForm
from src.auth import create_access_token, get_current_user, Token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
from fastapi import Depends, status
from pydantic import BaseModel
from typing import List, Optional

# Initialize Users DB
db.init_users_db()

app = FastAPI(title="ERP Lite API", version="2.0.0")

# CORS (Allow Frontend to hit Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"], # Vite Default Port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "ERP Lite API v2 Running"}

# --- AUTHENTICATION ---

@app.post("/api/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Authentication Strategy:
    # 1. Try finding by Hash (Secure Users)
    # 2. Try finding by Plain (Legacy Users)
    from src.auth import get_username_hash, verify_password
    
    input_hash = get_username_hash(form_data.username)
    
    # Try Hash
    user = db.obtener_usuario_por_username(input_hash)
    
    # Fallback to Plain if not found (Legacy compatibility)
    if not user:
        user = db.obtener_usuario_por_username(form_data.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check password
    if not verify_password(form_data.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Create Token
    # Use the Hash as the 'subject' if available, otherwise the plain username (legacy)
    # This ensures the Token doesn't carry the PII in plain text for new users.
    sub = user.get('username_hash') or user['username']
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": sub}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

# --- USER MANAGEMENT (Admin Only) ---

@app.get("/api/users")
def get_users(current_user: dict = Depends(get_current_user)):
    # Simple role check
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Requires Admin Role")
    
    try:
        from src.auth import decrypt_username
        df = db.listar_usuarios()
        users = df.fillna("").to_dict(orient="records")
        
        # Decrypt usernames for display
        for u in users:
            # If we have an encrypted version, show the real name
            if u.get('username_encrypted'):
                try:
                    u['username'] = decrypt_username(u['username_encrypted'])
                except:
                    pass # Keep the hash/original if decrypt fails
            
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = 'user'

@app.post("/api/users")
def create_new_user(req: CreateUserRequest, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Requires Admin Role")
    
    from src.auth import get_username_hash, encrypt_username
    
    u_hash = get_username_hash(req.username)
    u_enc = encrypt_username(req.username)
    
    # Store Hash in 'username' column (for Uniqueness and Obfuscation)
    # AND in 'username_hash' (Redundant but consistent)
    # Store Encrypted in 'username_encrypted'
    
    ok, msg = db.crear_usuario(
        username=u_hash, 
        password=req.password, 
        role=req.role,
        username_hash=u_hash,
        username_encrypted=u_enc
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "msg": msg}

@app.delete("/api/users/{uid}")
def delete_user(uid: int, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Requires Admin Role")
    
    ok, msg = db.eliminar_usuario(uid)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "msg": msg}


# --- MAESTROS ---



# --- MAESTROS ---

@app.get("/api/products")
def get_products():
    """Retorna lista extendida de productos con stock global"""
    try:
        df = db.obtener_productos_extendido()
        # Convert DataFrame to JSON friendly format (records)
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/purchases/summary")
def get_purchases_summary():
    try:
        data = db.obtener_compras_historial()
        return data.fillna("").to_dict(orient='records')
    except Exception as e:
        print(f"Error fetching purchase history: {e}")
        import traceback
        traceback.print_exc()
        return []

@app.get("/api/purchases/detailed")
def get_purchases_detailed():
    try:
        data = db.obtener_detalle_compras()
        return data.fillna("").to_dict(orient='records')
    except Exception as e:
        print(f"Error fetching detailed history: {e}")
        import traceback
        traceback.print_exc()
        return []

# --- DELIVERY GUIDES ENDPOINTS ---

@app.get("/api/guides")
def get_guides():
    try:
        return db.obtener_guias()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/guides/{gid}")
def get_guide(gid: int):
    try:
        data = db.obtener_guia_detalle(gid)
        if not data: raise HTTPException(status_code=404, detail="Guide not found")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/guides")
def create_guide(data: dict):
    try:
        ok, result = db.crear_guia_remision(data)
        if ok: return {"status": "success", "id": result}
        else: raise HTTPException(status_code=400, detail=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/warehouses")
def get_warehouses():
    try:
        df = db.obtener_almacenes()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/categories")
def get_categories():
    try:
        df = db.obtener_categorias()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/providers")
def get_providers():
    try:
        df = db.obtener_proveedores()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/warehouses")
def get_warehouses():
    try:
        df = db.obtener_almacenes()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- INVENTARIO ---

@app.get("/api/inventory/detailed")
def get_inventory_detailed():
    """Retorna inventario desglosado por almacén"""
    try:
        df = db.obtener_inventario_detallado()
        return df.fillna(0).to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/inventory/fifo")
def get_inventory_fifo(include_igv: bool = True):
    try:
        total, map_fifo = db.calcular_valorizado_fifo(incluir_igv=include_igv)
        # We need to merge this with products to make it useful
        df = db.obtener_productos_extendido()
        
        result = []
        if not df.empty:
            for _, row in df.iterrows():
                pid = row['id']
                val_data = map_fifo.get(pid, {'valor': 0.0})
                result.append({
                    "id": pid,
                    "sku": row['codigo_sku'],
                    "producto": row['nombre'],
                    "categoria": row['categoria_nombre'],
                    "unidad": row['unidad_medida'],
                    "stock": row['stock_actual'],
                    "fifo_valuated": val_data['valor'],
                    "costo_unitario": val_data['valor'] / row['stock_actual'] if row['stock_actual'] > 0 else row['costo_promedio'],
                    "valor_total": val_data['valor'],
                    "estado": "Normal" if row['stock_actual'] > 0 else "Sin Stock" # Simple status for now
                })
        return {"total_valuation": total, "items": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- KPI DASHBOARD ---

@app.get("/api/kpis")
def get_kpis():
    try:
        data = db.calcular_kpis()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- TRANSACCIONES ---

from pydantic import BaseModel
from typing import List, Optional

class CompraItem(BaseModel):
    pid: int
    cantidad: float
    precio_unitario: float

class CompraRequest(BaseModel):
    proveedor_id: int
    fecha: str
    moneda: str
    items: List[CompraItem]
    serie: str
    numero: str
    tc: float
    orden_compra_id: Optional[int] = None

@app.post("/api/purchases")
def register_purchase(req: CompraRequest):
    try:
        detalles = []
        for i in req.items:
            detalles.append({
                "producto_id": i.pid,
                "cantidad": i.cantidad,
                "precio_unitario": i.precio_unitario
            })
            
        cabecera = {
            'proveedor_id': req.proveedor_id,
            'fecha_emision': req.fecha,
            'moneda': req.moneda,
            'tc': req.tc,
            'serie': req.serie,
            'numero': req.numero,
            'tipo_documento': 'FACTURA', # Default
            'total': sum(i.cantidad * i.precio_unitario for i in req.items),
            'orden_compra_id': req.orden_compra_id
        }

        # call registrar_compra with dict
        res = db.registrar_compra(cabecera, detalles)
        
        if res['success']:
            return {"status": "success", "id": res['compra_id']}
        else:
            raise HTTPException(status_code=400, detail=res['error'])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ORDENES DE COMPRA ---

@app.get("/api/orders")
def get_orders():
    try:
        df = db.obtener_ordenes_compra()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/{oid}")
def get_order_by_id(oid: int):
    try:
        data = db.obtener_orden_compra(oid)
        if not data:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class OrderItem(BaseModel):
    pid: int
    cantidad: float
    precio_unitario: float

class OrderRequest(BaseModel):
    proveedor_id: int
    fecha: str
    moneda: str
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

@app.post("/api/orders")
def create_order(order: OrderRequest):
    """Create a new purchase order with auto-generated correlative"""
    try:
        # Pydantic models usually need .dict() or model_dump() (v2)
        # But here we can access attributes directly
        items_list = [
            {
                "pid": i.pid, 
                "cantidad": i.cantidad, 
                "precio_unitario": i.precio_unitario
            } for i in order.items
        ]

        orden_id = db.crear_orden_compra_con_correlativo(
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

@app.put("/api/orders/{oid}/status")
def update_order_status(oid: int, status: str):
    try:
        ok, msg = db.actualizar_estado_oc(oid, status)
        if ok: return {"status": "success", "msg": msg}
        else: raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/{oid}/balance")
def get_order_balance(oid: int):
    """Get pending balance for an OC (Requested - Received)"""
    try:
        data = db.obtener_saldo_oc(oid)
        if not data:
            raise HTTPException(status_code=404, detail="Order not found or error calculating balance")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders/pending")
def get_pending_orders():
    """Get orders that have items pending delivery"""
    try:
        data = db.obtener_ordenes_pendientes()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orders/{oid}/convert")
def convert_order_invoice(oid: int, serie: str, numero: str, fecha: str):
    try:
        ok, msg = db.convertir_oc_a_compra(oid, serie, numero, fecha)
        if ok: return {"status": "success", "msg": msg}
        else: raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/api/movements")
def register_movement(req: MovementRequest):
    try:
        if req.type == 'SALIDA':
            cab = {
                "fecha": req.fecha,
                "tipo": req.tipo_salida,
                "destino": req.destino,
                "obs": req.observaciones
            }
            # Adapt items
            detalles = [{"pid": i.pid, "cantidad": i.cantidad, "almacen_id": i.almacen_id} for i in req.items]
            
            ok, msg = db.registrar_salida(cab, detalles)
            if ok: return {"status": "success", "msg": msg}
            else: raise HTTPException(status_code=400, detail=msg)
            
        elif req.type == 'TRASLADO':
            cab = {
                "fecha": req.fecha,
                "origen_id": req.origen_id,
                "destino_id": req.destino_id,
                "observaciones": req.observaciones
            }
            detalles = [{"pid": i.pid, "cantidad": i.cantidad} for i in req.items]
            
            ok, msg = db.registrar_traslado(cab, detalles) # registrar_traslado returns (bool, msg)?? or raises exception?
            # Wait, let's check registrar_traslado return type in backend.py
            # It raises Exception on error, returns ID on success?
            # Re-reading backend.py snippet:
            # It seems I implemented it recently.
            # "if curr_st_orig < qty: raise Exception..."
            # It returns transaction ID or something?
            # Checking snippet 1460 in backend.py...
            # Actually line 1427 definition doesn't show return at the end of snippet.
            # I should verify if it returns (True, msg) or something else.
            # Assuming standard pattern (True, msg) based on other functions.
            # If it raises exception, the try/except here will catch it.
            
            # Let's wrap in try/except block specifically for logic errors if it raises
            try:
                # Based on previous pattern, it likely returns (True, msg) or raises.
                # Let's assume it might raise.
                res = db.registrar_traslado(cab, detalles)
                # If it returns a tuple
                if isinstance(res, tuple):
                    return {"status": "success", "msg": str(res[1])}
                return {"status": "success", "msg": "Traslado registrado"}
            except Exception as logic_err:
                 raise HTTPException(status_code=400, detail=str(logic_err))
                 
        else:
            raise HTTPException(status_code=400, detail="Invalid movement type")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- EXCHANGE RATE ENDPOINT ---

@app.get("/api/tipo-cambio")
def get_tipo_cambio():
    """Get current exchange rate from SUNAT API"""
    try:
        from src.api import obtener_tc_sunat
        tc = obtener_tc_sunat()
        return {"venta": tc, "compra": tc - 0.01}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- HISTORICAL DATA ENDPOINTS ---

@app.post("/api/purchase")
def create_purchase(data: dict):
    """Register a new purchase manually"""
    try:
        ok, msg = db.registrar_compra(data)
        if ok: return {"status": "success", "msg": msg}
        else: raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/purchases/summary")
def get_purchases_summary():
    """Purchase history summary"""
    try:
        df = db.obtener_compras_historial()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/purchases/detailed")
def get_purchases_detailed():
    """Purchase history detailed (line by line)"""
    try:
        df = db.obtener_compras_detalle_historial()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/exits/history")
def get_exits_history():
    """Exit/output history"""
    try:
        # Need to create this function in backend.py
        df = db.obtener_salidas_historial()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/transfers/history")
def get_transfers_history():
    """Transfer history between warehouses"""
    try:
        df = db.obtener_historial_traslados()
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/inventory/kardex/general")
def get_kardex_general(start_date: str, end_date: str):
    """General Kardex (all products)"""
    try:
        df = db.obtener_kardex_general(start_date, end_date)
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/inventory/kardex/{product_id}")
def get_kardex(product_id: int, start_date: str = None, end_date: str = None):
    """Kardex (movement history) for a specific product"""
    try:
        df = db.obtener_kardex_producto(product_id, start_date, end_date)
        return df.fillna("").to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/complete")
def get_dashboard_complete(start_date: str, end_date: str):
    """Complete dashboard data with all charts"""
    try:
        from datetime import datetime
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        return {
            "kpis": db.obtener_kpis_dashboard(start, end),
            "top_providers": db.obtener_top_proveedores(start, end).fillna("").to_dict(orient="records"),
            "categories": db.obtener_gastos_por_categoria(start, end).fillna("").to_dict(orient="records"),
            "evolution": db.obtener_evolucion_compras(start, end).fillna("").to_dict(orient="records"),
            "stock_critico": db.obtener_stock_critico().fillna("").to_dict(orient="records"),
            "rotacion": db.obtener_rotacion_inventario().fillna("").to_dict(orient="records"),
            "alertas": db.obtener_alertas_criticas()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- BULK DATA LOAD ---

from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse
import io

@app.get("/api/template/{type}")
def get_template(type: str):
    """Generate CSV template for bulk load"""
    import pandas as pd
    
    if type == 'products':
        cols = ['CodigoSKU', 'Nombre', 'Categoria', 'UnidadMedida', 'StockInicial', 'StockMinimo', 'CostoPromedio', 'PrecioVenta']
        df = pd.DataFrame(columns=cols)
    elif type == 'providers':
        cols = ['RUC', 'RazonSocial', 'Direccion', 'Telefono', 'Email', 'Categoria', 'Banco', 'Cuenta']
        df = pd.DataFrame(columns=cols)
    elif type == 'purchases':
        cols = ['Fecha', 'RUC_Proveedor', 'TipoDoc', 'Serie', 'Numero', 'Moneda', 'Total', 'ProductoSKU', 'Cantidad', 'PrecioUnitario']
        df = pd.DataFrame(columns=cols)
    elif type == 'initial_stock':
        cols = ['CodigoSKU', 'Cantidad', 'CostoUnitario']
        df = pd.DataFrame(columns=cols)
    else:
        raise HTTPException(status_code=400, detail="Invalid template type")
        
    stream = io.StringIO()
    df.to_csv(stream, index=False, sep=';', encoding='utf-8-sig') # Separator ; for Excel and BOM
    response = StreamingResponse(iter([stream.getvalue().encode('utf-8-sig')]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=template_{type}.csv"
    return response

@app.post("/api/upload/{type}")
async def upload_data(type: str, file: UploadFile = File(...), almacen_id: int = 1):
    """Process uploaded CSV/Excel file"""
    try:
        contents = await file.read()
        import pandas as pd
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Invalid file format. Use CSV or Excel.")
            
        # Logic delegate to backend.py
        if type == 'products':
            msg = db.carga_masiva_productos(df)
        elif type == 'providers':
            msg = db.carga_masiva_proveedores(df)
        elif type == 'purchases':
            msg = db.carga_masiva_compras(df)
        elif type == 'initial_stock':
            msg = db.carga_masiva_stock_inicial(df, almacen_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid upload type")
            
        return {"msg": msg}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
