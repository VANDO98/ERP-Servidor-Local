"""
Salidas Layout - Registro de salidas y servicios
"""

from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from datetime import datetime
from src import dashboard_backend as db


def create_layout():
    """Crea el layout del módulo de salidas"""
    
    return html.Div([
        html.H2([
            html.I(className="fas fa-box-open me-2"),
            "Registro de Salidas / Servicios"
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("📦 Tipo de Salida *", className="fw-bold"),
                        dcc.Dropdown(
                            id='salidas-tipo',
                            options=[
                                {'label': 'Servicio Técnico', 'value': 'servicio'},
                                {'label': 'Uso Interno', 'value': 'interno'},
                                {'label': 'Baja por Obsolescencia', 'value': 'baja'}
                            ],
                            placeholder="Seleccione tipo..."
                        )
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("🏢 Destino / Descripción *", className="fw-bold"),
                        dbc.Input(id='salidas-destino', type="text", placeholder="Ej: Obra Central, Oficina Lima")
                    ], width=4),
                    
                    dbc.Col([
                        html.Label("📅 Fecha *", className="fw-bold"),
                        dcc.DatePickerSingle(
                            id='salidas-fecha',
                            date=datetime.now().strftime('%Y-%m-%d'),
                            display_format='DD/MM/YYYY'
                        )
                    ], width=4)
                ])
            ])
        ], className="mb-4 shadow-sm"),
        
        html.H5("📋 Productos a Retirar", className="mb-3"),
        
        dbc.Card([
            dbc.CardBody([
                dag.AgGrid(
                    id='salidas-items-table',
                    columnDefs=[
                        {"field": "Producto", "headerName": "Producto", "editable": True, "flex": 2},
                        {"field": "StockActual", "headerName": "Stock Actual", "editable": False, "flex": 1},
                        {"field": "Cantidad", "headerName": "Cantidad Salida", "editable": True, "type": "numericColumn", "flex": 1}
                    ],
                    rowData=[],
                    className="ag-theme-alpine",
                    style={"height": 400}
                ),
                
                dbc.Button("➕ Agregar Producto", id="salidas-add-row", color="secondary", size="sm", className="mt-3")
            ])
        ], className="mb-4 shadow-sm"),
        
        dbc.Button([html.I(className="fas fa-save me-2"), "Registrar Salida"], id="salidas-save-btn", color="primary", size="lg"),
        
        html.Div(id='salidas-alerts', className="mt-3")
    ])
