
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import io
import pandas as pd
import uvicorn

# Import Modules
from src.database.db import init_db
from src.auth.router import router as auth_router
from src.inventory.router import router as inventory_router
from src.purchases.router import router as purchases_router
from src.dashboard.router import router as dashboard_router
from src.logistics.router import router as logistics_router
from src.backup.router import router as backup_router

# Import Services for Bulk Load (Legacy support or centralized)
from src.inventory import service as inv_service
from src.purchases import service as purch_service

app = FastAPI(title="ERP Lite API", version="3.0.0")

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173", "*"], # Incorrect for credentials with wildcard
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3})(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Startup ---
@app.on_event("startup")
def on_startup():
    init_db()

# --- Routers ---
app.include_router(auth_router)
app.include_router(inventory_router)
app.include_router(purchases_router)
app.include_router(dashboard_router)
app.include_router(logistics_router)
app.include_router(backup_router)

# --- Global Endpoints (Uploads & Templates) ---

@app.get("/")
def read_root():
    return {"status": "ok", "message": "ERP Lite API v3 (Modular) Running"}

@app.get("/api/template/{type}")
def get_template(type: str):
    """Generate CSV template for bulk load"""
    if type == 'products':
        cols = ['CodigoSKU', 'Nombre', 'Categoria', 'UnidadMedida', 'StockMinimo', 'CostoPromedio', 'PrecioVenta']
        df = pd.DataFrame(columns=cols)
    elif type == 'providers':
        cols = ['RUC', 'RazonSocial', 'Direccion', 'Telefono', 'Email', 'Categoria']
        df = pd.DataFrame(columns=cols)
    elif type == 'purchases':
        # Flattened structure for bulk: Header + Detail in one row
        cols = ['Fecha', 'RUC_Proveedor', 'Serie', 'Numero', 'Moneda', 'Total', 'ProductoSKU', 'Cantidad', 'PrecioUnitario']
        df = pd.DataFrame(columns=cols)
    elif type == 'initial_stock':
        cols = ['CodigoSKU', 'Cantidad', 'CostoUnitario']
        df = pd.DataFrame(columns=cols)
    else:
        raise HTTPException(status_code=400, detail="Invalid template type")
        
    stream = io.StringIO()
    df.to_csv(stream, index=False, sep=';', encoding='utf-8-sig')
    response = StreamingResponse(iter([stream.getvalue().encode('utf-8-sig')]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=template_{type}.csv"
    return response

@app.post("/api/upload/{type}")
async def upload_data(type: str, file: UploadFile = File(...), almacen_id: int = 1):
    """Process uploaded CSV/Excel file"""
    try:
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            # Try comma, then semicolon
            try:
                df = pd.read_csv(io.BytesIO(contents), sep=',')
                if len(df.columns) < 2: # heuristic check
                    df = pd.read_csv(io.BytesIO(contents), sep=';')
            except:
                df = pd.read_csv(io.BytesIO(contents), sep=';')
                
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Invalid file format. Use CSV or Excel.")
            
        # Delegate to Services
        msg = ""
        if type == 'products':
            msg = inv_service.carga_masiva_productos(df)
        elif type == 'providers':
            msg = purch_service.carga_masiva_proveedores(df)
        elif type == 'purchases':
            msg = purch_service.carga_masiva_compras(df)
        elif type == 'initial_stock':
            msg = inv_service.carga_masiva_stock_inicial(df, almacen_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid upload type")
            
        return {"msg": msg}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")

# --- Run ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
