"""
Aprovisionamiento Layout - Registro de órdenes de compra
"""

from dash import html, dcc, Input, Output, State, callback, dash_table, no_update, ctx
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import pandas as pd
from datetime import datetime
from src import dashboard_backend as db


def create_layout():
    """Crea el layout del módulo de aprovisionamiento"""
    
    proveedores = db.obtener_proveedores()
    # Obtener productos completos para mapa de unidades
    prods_full = db.obtener_productos_completo() 
    products_list = [p[1] for p in prods_full]
    products_data = {p[1]: p[3] for p in prods_full}
    
    return html.Div([
        dcc.Store(id='aprov-products-map', data=products_data),
        
        # Header
        html.H2([
            html.I(className="fas fa-truck me-2"),
            "Registro de Orden de Compra"
        ], className="mb-4"),
        
        # Formulario de cabecera
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("🏢 Proveedor *", className="fw-bold"),
                        dcc.Dropdown(
                            id='aprov-proveedor',
                            options=[{'label': p[1], 'value': p[0]} for p in proveedores],
                            placeholder="Seleccione un proveedor...",
                            className="mb-3"
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("📅 Fecha de Orden *", className="fw-bold"),
                        dcc.DatePickerSingle(
                            id='aprov-fecha',
                            date=datetime.now().strftime('%Y-%m-%d'),
                            display_format='DD/MM/YYYY',
                            className="w-100 mb-3"
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("💵 Moneda", className="fw-bold"),
                        dcc.Dropdown(
                            id='aprov-moneda',
                            options=[
                                {'label': 'PEN (Soles)', 'value': 'PEN'},
                                {'label': 'USD (Dólares)', 'value': 'USD'}
                            ],
                            value='PEN',
                            className="mb-3"
                        )
                    ], width=4)
                ])
            ])
        ], className="mb-4 shadow-sm"),
        
        # Tabla de items
        html.H5("📋 Detalle de Productos", className="mb-3"),
        
        dbc.Card([
            dbc.CardBody([
                dag.AgGrid(
                    id='aprov-items-table',
                    columnDefs=[
                        {
                            "field": "Producto",
                            "headerName": "Producto",
                            "editable": True,
                            "cellEditor": "agSelectCellEditor",
                            "cellEditorParams": {
                                "values": products_list
                            },
                            "flex": 2
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
                            "valueSetter": {"function": "data.Cantidad = Number(newValue); data.Total = Number(data.Cantidad) * Number(data.PrecioUnitario); return true;"},
                            "flex": 1
                        },
                        {
                            "field": "PrecioUnitario",
                            "headerName": "Precio Unit.",
                            "editable": True,
                            "type": "numericColumn",
                            "valueFormatter": {"function": "d3.format(',.2f')(params.value)"},
                            "valueSetter": {"function": "data.PrecioUnitario = Number(newValue); data.Total = Number(data.Cantidad) * Number(data.PrecioUnitario); return true;"},
                            "flex": 1
                        },
                        {
                            "field": "Total",
                            "headerName": "Total",
                            "editable": False,
                            "type": "numericColumn",
                            "valueFormatter": {"function": "d3.format(',.2f')(params.value)"},
                            "valueGetter": {"function": "Number(data.Cantidad) * Number(data.PrecioUnitario)"},
                            "flex": 1,
                            "cellStyle": {"fontWeight": "bold"}
                        }
                    ],
                    rowData=[],
                    defaultColDef={
                        "resizable": True,
                        "sortable": True
                    },
                    dashGridOptions={
                        "singleClickEdit": True,
                        "stopEditingWhenCellsLoseFocus": True,
                        "rowSelection": "multiple",
                        "animateRows": True
                    },
                    className="ag-theme-alpine",
                    style={"height": 400}
                ),
                
                dbc.ButtonGroup([
                    dbc.Button([
                        html.I(className="fas fa-plus me-2"),
                        "Agregar Fila"
                    ], id="aprov-add-row", color="secondary", size="sm", className="mt-3"),
                    
                    dbc.Button([
                        html.I(className="fas fa-trash me-2"),
                        "Eliminar Seleccionadas"
                    ], id="aprov-delete-rows", color="danger", size="sm", className="mt-3 ms-2")
                ])
            ])
        ], className="mb-4 shadow-sm"),
        
        # Totales y acciones
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Resumen", className="mb-3"),
                        html.Div([
                            html.Strong("Subtotal: "),
                            html.Span(id='aprov-subtotal', children="S/ 0.00")
                        ], className="mb-2"),
                        html.Hr(),
                        html.Div([
                            html.Strong("Total: ", className="fs-5"),
                            html.Span(id='aprov-total', children="S/ 0.00", className="fs-5 text-primary")
                        ])
                    ])
                ], className="shadow-sm")
            ], width=4),
            
            dbc.Col([
                html.Div([
                    dbc.Button([
                        html.I(className="fas fa-save me-2"),
                        "Registrar Orden de Compra"
                    ], id="aprov-save-btn", color="primary", size="lg", className="w-100")
                ], className="d-flex align-items-end h-100")
            ], width=8)
        ]),
        
        # Alerts
        html.Div(id='aprov-alerts', className="mt-3")
    ])


# Callbacks
@callback(
    Output('aprov-items-table', 'rowData'),
    [Input('aprov-add-row', 'n_clicks'),
     Input('aprov-items-table', 'cellValueChanged'),
     Input('aprov-delete-rows', 'n_clicks')],
    [State('aprov-items-table', 'rowData'),
     State('aprov-items-table', 'selectedRows'),
     State('aprov-products-map', 'data')],
    prevent_initial_call=True
)
def update_rows(add_clicks, cell_change, delete_clicks, current_data, selected_rows, products_map):
    """Maneja agregar, eliminar y actualizar unidades"""
    ctx_triggered = ctx.triggered_id
    
    if current_data is None: current_data = []

    if ctx_triggered == 'aprov-add-row':
        current_data.append({
            "Producto": "",
            "Unidad": "UND",
            "Cantidad": 0,
            "PrecioUnitario": 0.0,
            "Total": 0.0
        })
        return current_data
        
    if ctx_triggered == 'aprov-delete-rows':
        if not selected_rows: return current_data
        return [row for row in current_data if row not in selected_rows]

    if ctx_triggered == 'aprov-items-table':
        if not products_map: return no_update
        updated = False
        for row in current_data:
            prod_name = row.get('Producto')
            if prod_name and prod_name in products_map:
                unit = products_map[prod_name]
                if row.get('Unidad') != unit:
                    row['Unidad'] = unit
                    updated = True
        return current_data if updated else no_update
        
    return no_update


@callback(
    [Output('aprov-subtotal', 'children'),
     Output('aprov-total', 'children')],
    [Input('aprov-items-table', 'cellValueChanged'),
     Input('aprov-items-table', 'rowData')],
    State('aprov-moneda', 'value')
)
def update_totals(cell_change, row_data, moneda):
    """Actualiza los totales según los items"""
    if not row_data:
        return "S/ 0.00", "S/ 0.00"
    
    # Calcular en Python para asegurar
    subtotal = 0
    for row in row_data:
        cant = float(row.get('Cantidad', 0) or 0)
        precio = float(row.get('PrecioUnitario', 0) or 0)
        subtotal += cant * precio
        
    simbolo = "S/" if moneda == 'PEN' else "$"
    
    return f"{simbolo} {subtotal:,.2f}", f"{simbolo} {subtotal:,.2f}"


@callback(
    Output('aprov-alerts', 'children'),
    Input('aprov-save-btn', 'n_clicks'),
    [State('aprov-proveedor', 'value'),
     State('aprov-fecha', 'date'),
     State('aprov-moneda', 'value'),
     State('aprov-items-table', 'rowData')],
    prevent_initial_call=True
)
def save_orden(n_clicks, proveedor, fecha, moneda, items):
    """Guarda la orden de compra en la base de datos"""
    
    # Validaciones
    if not proveedor:
        return dbc.Alert("⚠️ Debe seleccionar un proveedor", color="warning", dismissable=True)
    
    if not items or len(items) == 0:
        return dbc.Alert("⚠️ Debe agregar al menos un producto", color="warning", dismissable=True)
    
    # Validar que todos los items tengan datos
    items_valid = []
    for item in items:
        if item.get('Producto'):
             items_valid.append(item)
             
    if not items_valid:
        return dbc.Alert("⚠️ Todos los productos deben tener nombre", color="warning", dismissable=True)
    
    try:
        # Registrar en BD
        resultado = db.registrar_orden_compra(proveedor, fecha, moneda, items_valid)
        
        if resultado['success']:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"✅ Orden registrada exitosamente. ID: {resultado['orden_id']}"
            ], color="success", dismissable=True, duration=5000)
        else:
            return dbc.Alert(f"❌ Error: {resultado['error']}", color="danger", dismissable=True)
            
    except Exception as e:
        return dbc.Alert(f"❌ Error al guardar: {str(e)}", color="danger", dismissable=True)
