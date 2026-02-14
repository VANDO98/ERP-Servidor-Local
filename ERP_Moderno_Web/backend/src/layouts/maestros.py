"""
Maestros Layout - Configuración de productos, categorías y proveedores
"""

from dash import html, dcc, Input, Output, State, callback, no_update
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from src import dashboard_backend as db


def create_layout():
    """Crea el layout del módulo de maestros"""
    
    return html.Div([
        html.H2([
            html.I(className="fas fa-cogs me-2"),
            "Configuración de Maestros"
        ], className="mb-4"),
        
        dbc.Tabs([
            dbc.Tab(label="📦 Productos", tab_id="tab-productos"),
            dbc.Tab(label="📂 Categorías", tab_id="tab-categorias"),
            dbc.Tab(label="🏢 Proveedores", tab_id="tab-proveedores")
        ], id="maestros-tabs", active_tab="tab-productos"),
        
        html.Div(id="maestros-content", className="mt-4")
    ])


@callback(
    Output('maestros-content', 'children'),
    Input('maestros-tabs', 'active_tab')
)
def render_maestros_content(active_tab):
    """Renderiza el contenido según la pestaña activa"""
    
    if active_tab == "tab-productos":
        return render_productos_tab()
    elif active_tab == "tab-categorias":
        return render_categorias_tab()
    elif active_tab == "tab-proveedores":
        return render_proveedores_tab()


def render_productos_tab():
    """Tab de gestión de productos"""
    
    categorias = db.obtener_categorias()
    productos = db.obtener_productos_completo()
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("➕ Agregar Nuevo Producto", className="fw-bold"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("SKU / Código *"),
                                dbc.Input(id='prod-sku', type="text", placeholder="SKU-001")
                            ], width=4),
                            dbc.Col([
                                html.Label("Nombre del Producto *"),
                                dbc.Input(id='prod-nombre', type="text", placeholder="Ej: Laptop HP 15-dy2021la")
                            ], width=8),
                        ], className="mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                html.Label("Categoría *"),
                                dcc.Dropdown(
                                    id='prod-categoria',
                                    options=[{'label': c[1], 'value': c[0]} for c in categorias],
                                    placeholder="Seleccione..."
                                )
                            ], width=6),
                            
                            dbc.Col([
                                html.Label("Unidad de Medida"),
                                dcc.Dropdown(
                                    id='prod-unidad',
                                    options=[
                                        {'label': 'Unidad (UND)', 'value': 'UND'},
                                        {'label': 'Caja (CAJ)', 'value': 'CAJ'},
                                        {'label': 'Paquete (PAQ)', 'value': 'PAQ'},
                                        {'label': 'Kilogramo (KG)', 'value': 'KG'},
                                        {'label': 'Litro (LTR)', 'value': 'LTR'},
                                        {'label': 'Metro (MTR)', 'value': 'MTR'}
                                    ],
                                    value='UND'
                                )
                            ], width=6),
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col([
                                html.Label("Stock Inicial"),
                                dbc.Input(id='prod-stock', type="number", value=0, min=0)
                            ], width=6)
                        ]),
                        
                        dbc.Button([html.I(className="fas fa-plus me-2"), "Agregar Producto"], 
                                   id="prod-add-btn", color="primary", className="mt-3"),
                        
                        html.Div(id='prod-msg', className="mt-3")
                    ])
                ], className="shadow-sm mb-4")
            ], width=12)
        ]),
        
        dbc.Card([
            dbc.CardHeader("📋 Listado de Productos", className="fw-bold"),
            dbc.CardBody([
                dag.AgGrid(
                    id='productos-table',
                    columnDefs=[
                        {"field": "ID", "headerName": "ID", "flex": 0.5},
                        {"field": "Nombre", "headerName": "Nombre", "flex": 2},
                        {"field": "categoria", "headerName": "Categoría", "flex": 1},
                        {"field": "unidad_medida", "headerName": "U.M.", "flex": 0.5},
                        {"field": "stock", "headerName": "Stock", "type": "numericColumn", "flex": 0.7}
                    ],
                    rowData=[dict(zip(['ID', 'Nombre', 'categoria', 'unidad_medida', 'stock'], p)) for p in productos],
                    className="ag-theme-alpine",
                    style={"height": 400},
                    defaultColDef={"resizable": True, "sortable": True, "filter": True}
                )
            ])
        ], className="shadow-sm")
    ])


def render_categorias_tab():
    """Tab de gestión de categorías"""
    
    categorias = db.obtener_categorias()
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("➕ Agregar Nueva Categoría", className="fw-bold"),
                    dbc.CardBody([
                        dbc.Input(id='cat-nombre', type="text", placeholder="Nombre de la categoría", className="mb-3"),
                        dbc.Button([html.I(className="fas fa-plus me-2"), "Agregar"], id="cat-add-btn", color="primary"),
                        html.Div(id='cat-msg', className="mt-3")
                    ])
                ], className="shadow-sm mb-4")
            ], width=6)
        ]),
        
        dbc.Card([
            dbc.CardHeader("📂 Categorías Existentes", className="fw-bold"),
            dbc.CardBody([
                dbc.ListGroup([
                    dbc.ListGroupItem(cat[1]) for cat in categorias
                ])
            ])
        ], className="shadow-sm")
    ])


def render_proveedores_tab():
    """Tab de gestión de proveedores"""
    
    proveedores = db.obtener_proveedores_completo()
    
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("➕ Agregar Nuevo Proveedor (Completo)", className="fw-bold"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("RUC *"),
                                dbc.Input(id='prov-ruc', type="text", placeholder="20123456789", maxLength=11)
                            ], width=4),
                            
                            dbc.Col([
                                html.Label("Razón Social *"),
                                dbc.Input(id='prov-razon', type="text", placeholder="EMPRESA S.A.C.")
                            ], width=8)
                        ], className="mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                html.Label("Dirección"),
                                dbc.Input(id='prov-dir', type="text", placeholder="Av. Principal 123")
                            ], width=12)
                        ], className="mb-3"),
                        
                        dbc.Row([
                            dbc.Col([
                                html.Label("Teléfono"),
                                dbc.Input(id='prov-tel', type="text", placeholder="999888777")
                            ], width=4),
                            
                            dbc.Col([
                                html.Label("Email"),
                                dbc.Input(id='prov-email', type="email", placeholder="contacto@empresa.com")
                            ], width=4),
                             
                            dbc.Col([
                                html.Label("Contacto"),
                                dbc.Input(id='prov-contacto', type="text", placeholder="Nombre Contacto")
                            ], width=4),
                        ], className="mb-3"),
                        
                        dbc.Button([html.I(className="fas fa-plus me-2"), "Agregar Proveedor"], id="prov-add-btn", color="primary"),
                        html.Div(id='prov-msg', className="mt-3")
                    ])
                ], className="shadow-sm mb-4")
            ], width=12)
        ]),
        
        dbc.Card([
            dbc.CardHeader("🏢 Proveedores Registrados", className="fw-bold"),
            dbc.CardBody([
                dag.AgGrid(
                    id='proveedores-table',
                    columnDefs=[
                        {"field": "ID", "headerName": "ID", "width": 70},
                        {"field": "RUC", "headerName": "RUC", "width": 120},
                        {"field": "RazonSocial", "headerName": "Razón Social", "flex": 2}
                    ],
                    rowData=[dict(zip(['ID', 'RUC', 'RazonSocial'], p)) for p in proveedores],
                    className="ag-theme-alpine",
                    style={"height": 400},
                    defaultColDef={"resizable": True, "sortable": True, "filter": True}
                )
            ])
        ], className="shadow-sm")
    ])

# Callbacks CRUD

@callback(
    Output('prod-msg', 'children'),
    Input('prod-add-btn', 'n_clicks'),
    [State('prod-sku', 'value'),
     State('prod-nombre', 'value'),
     State('prod-categoria', 'value'),
     State('prod-unidad', 'value'),
     State('prod-stock', 'value')],
    prevent_initial_call=True
)
def add_producto(n, sku, nombre, cat_id, unidad, stock):
    if not n: return no_update
    if not nombre or not cat_id or not sku:
        return dbc.Alert("⚠️ Falta SKU, Nombre o Categoría", color="warning", dismissable=True)
    
    ok, msg, pid = db.crear_producto(sku, nombre, unidad, cat_id, int(stock) if stock else 0)
    if ok:
        return dbc.Alert(f"✅ {msg}", color="success", dismissable=True)
    else:
        return dbc.Alert(f"❌ {msg}", color="danger", dismissable=True)

@callback(
    Output('cat-msg', 'children'),
    Input('cat-add-btn', 'n_clicks'),
    State('cat-nombre', 'value'),
    prevent_initial_call=True
)
def add_categoria(n, nombre):
    if not n: return no_update
    if not nombre:
         return dbc.Alert("⚠️ Ingrese nombre", color="warning", dismissable=True)
         
    ok, msg = db.crear_categoria(nombre)
    if ok:
        return dbc.Alert(f"✅ {msg}", color="success", dismissable=True)
    else:
        return dbc.Alert(f"❌ {msg}", color="danger", dismissable=True)

@callback(
    Output('prov-msg', 'children'),
    Input('prov-add-btn', 'n_clicks'),
    [State('prov-ruc', 'value'),
     State('prov-razon', 'value'),
     State('prov-dir', 'value'),
     State('prov-tel', 'value'),
     State('prov-email', 'value'),
     State('prov-contacto', 'value')],
    prevent_initial_call=True
)
def add_proveedor(n, ruc, razon, direccion, telefono, email, contacto):
    if not n: return no_update
    if not ruc or not razon:
        return dbc.Alert("⚠️ Falta RUC o Razón Social", color="warning", dismissable=True)
        
    ok, msg = db.crear_proveedor(ruc, razon, direccion or '', telefono or '', email or '', contacto or '')
    if ok:
        return dbc.Alert(f"✅ {msg}", color="success", dismissable=True)
    else:
        return dbc.Alert(f"❌ {msg}", color="danger", dismissable=True)
