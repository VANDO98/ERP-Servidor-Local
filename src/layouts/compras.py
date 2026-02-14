"""
Compras Layout - Registro de facturas, compras e historial
"""

from dash import html, dcc, Input, Output, State, callback, dash_table, no_update, ctx
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from datetime import date, timedelta, datetime
from src import dashboard_backend as db
import pandas as pd

def create_layout():
    """Crea el layout del módulo de compras con pestañas"""
    
    return html.Div([
        html.H2([
            html.I(className="fas fa-shopping-cart me-2"),
            "Gestión de Compras"
        ], className="mb-4"),
        
        # Store para info de productos (Unidades, Precios ref?)
        dcc.Store(id='compras-products-store'),
        
        dbc.Tabs([
            dbc.Tab(label="📝 Registrar Compra", tab_id="tab-registro"),
            dbc.Tab(label="📜 Historial Facturas", tab_id="tab-historial"),
            dbc.Tab(label="🔍 Historial Detallado", tab_id="tab-detalle"),
        ], id="compras-tabs", active_tab="tab-registro"),
        
        html.Div(id="compras-content", className="mt-4")
    ])


@callback(
    Output('compras-content', 'children'),
    [Input('compras-tabs', 'active_tab'),
     Input('global-date-range', 'start_date'),
     Input('global-date-range', 'end_date')]
)
def render_content(active_tab, start_date, end_date):
    """Renderiza el contenido según la pestaña activa"""
    trigger = ctx.triggered_id
    
    # Si cambia fecha y no es tab historial/detalle, no hacer nada (optimización)
    if 'global' in str(trigger) and active_tab == 'tab-registro':
        return no_update

    if active_tab == "tab-registro":
        return render_registro_tab()
    elif active_tab == "tab-historial":
        return render_historial_tab(start_date, end_date)
    elif active_tab == "tab-detalle":
        return render_detalle_tab(start_date, end_date)
    return html.Div("Seleccione una pestaña")


def render_registro_tab():
    proveedores = db.obtener_proveedores()
    # Obtener productos completos para mapa de unidades
    prods_full = db.obtener_productos_completo() # [(id, nombre, cat, um, stock), ...]
    products_list = [p[1] for p in prods_full]
    
    # Store data for callbacks
    products_data = {p[1]: p[3] for p in prods_full} # Name -> Unit
    
    return html.Div([
        dcc.Store(id='local-products-map', data=products_data),
        
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("🏢 Proveedor *", className="fw-bold"),
                        dcc.Dropdown(
                            id='compras-proveedor',
                            options=[{'label': p[1], 'value': p[0]} for p in proveedores],
                            placeholder="Seleccione un proveedor..."
                        )
                    ], width=4),
                    
                    # Split Factura: Serie - Correlativo
                    dbc.Col([
                        html.Label("📄 Serie", className="fw-bold"),
                        dbc.Input(id='compras-serie', type="text", placeholder="F001", maxLength=4)
                    ], width=2),
                    
                    dbc.Col([
                        html.Label("📄 Número", className="fw-bold"),
                        dbc.Input(id='compras-numero', type="text", placeholder="0001234", maxLength=8)
                    ], width=3),
                    
                    dbc.Col([
                        html.Label("📅 Fecha de Emisión *", className="fw-bold"),
                        dcc.DatePickerSingle(
                            id='compras-fecha',
                            date=date.today(),
                            display_format='DD/MM/YYYY',
                            className="w-100"
                        )
                    ], width=3)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        html.Label("💵 Moneda", className="fw-bold"),
                        dcc.Dropdown(
                            id='compras-moneda',
                            options=[
                                {'label': 'PEN (Soles)', 'value': 'PEN'},
                                {'label': 'USD (Dólares)', 'value': 'USD'}
                            ],
                            value='PEN'
                        )
                    ], width=3),
                    
                    dbc.Col([
                        html.Label("📊 IGV (%)", className="fw-bold"),
                        dbc.Input(id='compras-igv', type="number", value=18, min=0, max=100)
                    ], width=3),
                    
                    dbc.Col([
                         html.Label("📝 Obs.", className="fw-bold"),
                         dbc.Input(id='compras-obs', type="text", placeholder="Observaciones...")
                    ], width=6)
                ])
            ])
        ], className="mb-4 shadow-sm"),
        
        html.H5("📋 Detalle de Productos", className="mb-3"),
        
        dbc.Card([
            dbc.CardBody([
                dag.AgGrid(
                    id='compras-items-table',
                    columnDefs=[
                        {
                            "field": "Producto", 
                            "headerName": "Producto", 
                            "editable": True, 
                            "flex": 2,
                            "cellEditor": "agSelectCellEditor",
                            "cellEditorParams": {
                                "values": products_list
                            }
                        },
                        {
                            "field": "Unidad", 
                            "headerName": "UM", 
                            "editable": False, 
                            "width": 80,
                            "cellStyle": {'backgroundColor': '#f8f9fa'}
                        },
                        {
                            "field": "Cantidad", 
                            "headerName": "Cantidad", 
                            "editable": True, 
                            "type": "numericColumn", 
                            "flex": 1,
                            "valueSetter": {"function": "data.Cantidad = Number(newValue); data.Total = Number(data.Cantidad) * Number(data.PrecioUnitario); return true;"}
                        },
                        {
                            "field": "PrecioUnitario", 
                            "headerName": "Precio Unit.", 
                            "editable": True, 
                            "type": "numericColumn", 
                            "flex": 1,
                            "valueSetter": {"function": "data.PrecioUnitario = Number(newValue); data.Total = Number(data.Cantidad) * Number(data.PrecioUnitario); return true;"},
                            "valueFormatter": {"function": "d3.format(',.2f')(params.value)"}
                        },
                        {
                            "field": "Total", 
                            "headerName": "Total", 
                            "editable": False, 
                            "type": "numericColumn", 
                            "flex": 1,
                            "valueGetter": {"function": "Number(data.Cantidad) * Number(data.PrecioUnitario)"},
                            "valueFormatter": {"function": "d3.format(',.2f')(params.value)"}
                        }
                    ],
                    rowData=[],
                    defaultColDef={"resizable": True, "sortable": True},
                    dashGridOptions={
                        "singleClickEdit": True,
                        "stopEditingWhenCellsLoseFocus": True
                    },
                    className="ag-theme-alpine",
                    style={"height": 400}
                ),
                
                dbc.ButtonGroup([
                    dbc.Button([html.I(className="fas fa-plus me-2"), "Agregar Fila"], id="compras-add-row", color="secondary", size="sm", className="mt-3"),
                    dbc.Button([html.I(className="fas fa-trash me-2"), "Limpiar"], id="compras-clear-rows", color="danger", size="sm", className="mt-3 ms-2")
                ])
            ])
        ], className="mb-4 shadow-sm"),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([html.Strong("Subtotal: "), html.Span(id='compras-subtotal', children="S/ 0.00")]),
                        html.Div([html.Strong("IGV: "), html.Span(id='compras-igv-monto', children="S/ 0.00")]),
                        html.Hr(),
                        html.Div([html.Strong("Total: ", className="fs-5"), html.Span(id='compras-total', children="S/ 0.00", className="fs-5 text-primary")])
                    ])
                ])
            ], width=4),
            
            dbc.Col([
                dbc.Button([html.I(className="fas fa-save me-2"), "Registrar Factura"], id="compras-save-btn", color="primary", size="lg", className="w-100")
            ], width=8)
        ]),
        
        html.Div(id='compras-alerts', className="mt-3")
    ])


def render_historial_tab(start_date, end_date):
    """Renderiza tabla de historial de facturas"""
    # Usar fechas globales si existen, sino default
    if not start_date or not end_date:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
    historial = db.obtener_compras_historial() # TODO: filtrar por fechas en backend si se desea optimizar
    # Filtramos en Python por ahora ya que la funcion backend trae todo (simple)
    # Validar formato fecha
    
    # Convertir a DF para filtrar rapido
    df = pd.DataFrame(historial, columns=['id', 'fecha', 'numero_documento', 'proveedor', 'moneda', 'total_final', 'items'])
    if not df.empty and start_date and end_date:
         df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce')
         mask = (df['fecha_dt'] >= pd.to_datetime(start_date)) & (df['fecha_dt'] <= pd.to_datetime(end_date))
         df = df.loc[mask]
    
    col_defs = [
        {"field": "id", "headerName": "ID", "width": 70},
        {"field": "fecha", "headerName": "Fecha", "width": 120},
        {"field": "numero_documento", "headerName": "Nro Documento", "flex": 1},
        {"field": "proveedor", "headerName": "Proveedor", "flex": 1},
        {"field": "moneda", "headerName": "Moneda", "width": 100},
        {"field": "total_final", "headerName": "Total", "type": "numericColumn", "valueFormatter": {"function": "d3.format(',.2f')(params.value)"}},
        {"field": "items", "headerName": "Items", "width": 80}
    ]
    
    return dbc.Card([
        dbc.CardBody([
            dag.AgGrid(
                columnDefs=col_defs,
                rowData=df.to_dict('records'),
                className="ag-theme-alpine",
                defaultColDef={"filter": True, "sortable": True},
                style={"height": 600}
            )
        ])
    ])


def render_detalle_tab(start_date, end_date):
    """Renderiza tabla detallada de items"""
    detalle = db.obtener_compras_detalle_historial()
    
    df = pd.DataFrame(detalle, columns=['fecha', 'numero_documento', 'proveedor', 'producto', 'cantidad', 'precio_unitario', 'subtotal', 'moneda', 'compra_id'])
    
    if not df.empty and start_date and end_date:
         df['fecha_dt'] = pd.to_datetime(df['fecha'], errors='coerce')
         mask = (df['fecha_dt'] >= pd.to_datetime(start_date)) & (df['fecha_dt'] <= pd.to_datetime(end_date))
         df = df.loc[mask]
    
    col_defs = [
        {"field": "fecha", "headerName": "Fecha", "width": 120},
        {"field": "numero_documento", "headerName": "Doc", "width": 120},
        {"field": "proveedor", "headerName": "Proveedor", "flex": 1},
        {"field": "producto", "headerName": "Producto", "flex": 1},
        {"field": "cantidad", "headerName": "Cant.", "width": 90},
        {"field": "precio_unitario", "headerName": "P. Unit", "width": 100, "valueFormatter": {"function": "d3.format(',.2f')(params.value)"}},
        {"field": "subtotal", "headerName": "Subtotal", "width": 100, "valueFormatter": {"function": "d3.format(',.2f')(params.value)"}},
        {"field": "moneda", "headerName": "Mon", "width": 80},
    ]
    
    return dbc.Card([
        dbc.CardBody([
            dag.AgGrid(
                columnDefs=col_defs,
                rowData=df.to_dict('records'),
                className="ag-theme-alpine",
                defaultColDef={"filter": True, "sortable": True},
                style={"height": 600}
            )
        ])
    ])


# Callbacks de funcionalidad en Registro

@callback(
    Output('compras-items-table', 'rowData'),
    [Input('compras-add-row', 'n_clicks'),
     Input('compras-clear-rows', 'n_clicks'),
     Input('compras-items-table', 'cellValueChanged')], # Escuchar cambios de celda para autocompletar unidad
    [State('compras-items-table', 'rowData'),
     State('local-products-map', 'data')],
    prevent_initial_call=True
)
def update_rows(add_clicks, clear_clicks, cell_change, current_data, products_map):
    ctx_triggered = ctx.triggered_id
    
    if current_data is None: current_data = []

    # Caso 1: Agregar fila
    if ctx_triggered == 'compras-add-row':
        current_data.append({"Producto": "", "Unidad": "UND", "Cantidad": 0, "PrecioUnitario": 0.0, "Total": 0.0})
        return current_data
        
    # Caso 2: Limpiar
    if ctx_triggered == 'compras-clear-rows':
        return []
    
    # Caso 3: Cambio de celda (Autocompletar Unidad)
    if ctx_triggered == 'compras-items-table':
        # cell_change trae informacion de que celda cambio, pero rowData trae el estado actual
        # Iteramos para validar unidades
        if not products_map: return no_update
        
        updated = False
        for row in current_data:
            prod_name = row.get('Producto')
            if prod_name and prod_name in products_map:
                unit = products_map[prod_name]
                if row.get('Unidad') != unit:
                    row['Unidad'] = unit
                    updated = True
        
        if updated:
            return current_data
        
    return no_update


@callback(
    [Output('compras-subtotal', 'children'),
     Output('compras-igv-monto', 'children'),
     Output('compras-total', 'children')],
    [Input('compras-items-table', 'cellValueChanged'),
     Input('compras-items-table', 'rowData'),
     Input('compras-igv', 'value')],
    State('compras-moneda', 'value'),
    prevent_initial_call=True
)
def update_totals(cell_change, row_data, igv_percent, moneda):
    if not row_data:
        simbolo = "S/" if moneda == 'PEN' else "$"
        return f"{simbolo} 0.00", f"{simbolo} 0.00", f"{simbolo} 0.00"
    
    subtotal = 0
    for row in row_data:
        cant = float(row.get('Cantidad', 0) or 0)
        precio = float(row.get('PrecioUnitario', 0) or 0)
        subtotal += cant * precio
    
    igv_percent = float(igv_percent or 18)
    igv = subtotal * (igv_percent / 100)
    total = subtotal + igv
    
    simbolo = "S/" if moneda == 'PEN' else "$"
    
    return f"{simbolo} {subtotal:,.2f}", f"{simbolo} {igv:,.2f}", f"{simbolo} {total:,.2f}"


@callback(
    Output('compras-alerts', 'children'),
    Input('compras-save-btn', 'n_clicks'),
    [State('compras-proveedor', 'value'),
     State('compras-serie', 'value'),
     State('compras-numero', 'value'),
     State('compras-fecha', 'date'),
     State('compras-moneda', 'value'),
     State('compras-igv', 'value'),
     State('compras-obs', 'value'),
     State('compras-items-table', 'rowData')],
    prevent_initial_call=True
)
def save_compra(n_clicks, proveedor_id, serie, numero, fecha, moneda, igv, obs, items):
    if not n_clicks: return no_update
    
    if not proveedor_id or not serie or not numero or not fecha:
        return dbc.Alert("⚠️ Falta completar Proveedor, Serie, Número o Fecha", color="warning", dismissable=True)
    
    if not items:
        return dbc.Alert("⚠️ No hay items en la compra", color="warning", dismissable=True)
    
    # Concatenar Doc
    full_doc = f"{serie}-{numero}"
    
    # Calcular totales final
    subtotal = sum([(float(x.get('Cantidad', 0) or 0) * float(x.get('PrecioUnitario', 0) or 0)) for x in items])
    total = subtotal * (1 + (float(igv)/100))
    
    cabecera = {
        'proveedor_id': proveedor_id,
        'fecha': fecha,
        'numero_documento': full_doc,
        'moneda': moneda,
        'total': total,
        'observaciones': obs or ''
    }
    
    items_to_save = []
    for item in items:
        if not item.get('Producto'): continue
        items_to_save.append({
            'Producto': item['Producto'],
            'cantidad': float(item.get('Cantidad', 0)),
            'precio_unitario': float(item.get('PrecioUnitario', 0)),
            'total': float(item.get('Cantidad', 0)) * float(item.get('PrecioUnitario', 0)),
            'unidad': item.get('Unidad', 'UND') 
        })
    
    if not items_to_save:
        return dbc.Alert("⚠️ Items inválidos (sin producto)", color="warning", dismissable=True)

    result = db.registrar_compra(cabecera, items_to_save)
    
    if result['success']:
        return dbc.Alert(f"✅ Compra registrada correctamente. ID: {result['compra_id']}", color="success", dismissable=True)
    else:
        return dbc.Alert(f"❌ Error al registrar: {result['error']}", color="danger", dismissable=True)
