"""
Inventario Layout - Consulta de kardex y valorización
"""

from dash import html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.graph_objects as go
from src import dashboard_backend as db
from datetime import date, timedelta

def create_layout():
    """Crea el layout del módulo de inventario"""
    
    productos = db.obtener_productos()
    
    # Nota: El filtro de fechas es GLOBAL desde el Sidebar (global-date-range)
    
    return html.Div([
        html.H2([
            html.I(className="fas fa-warehouse me-2"),
            "Consulta de Inventario y Kardex"
        ], className="mb-4"),
        
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("🔍 Seleccione Producto", className="fw-bold"),
                        dcc.Dropdown(
                            id='inv-producto',
                            options=[{'label': p[1], 'value': p[0]} for p in productos],
                            placeholder="Buscar producto...",
                            className="mb-3"
                        )
                    ], width=12),
                ])
            ])
        ], className="mb-4 shadow-sm"),
        
        # KPIs del producto
        html.Div(id='inv-kpis', className="mb-4"),
        
        # Tabla de movimientos (Kardex)
        html.H5("📋 Movimientos (Kardex)", className="mb-3"),
        
        dbc.Card([
            dbc.CardBody([
                dag.AgGrid(
                    id='inv-kardex-table',
                    columnDefs=[
                        {"field": "Fecha", "headerName": "Fecha", "flex": 1},
                        {"field": "TipoMovimiento", "headerName": "Tipo", "flex": 1},
                        {"field": "Documento", "headerName": "Documento", "flex": 1},
                        {"field": "Entradas", "headerName": "Entradas", "type": "numericColumn", "flex": 1},
                        {"field": "Salidas", "headerName": "Salidas", "type": "numericColumn", "flex": 1},
                        {"field": "Saldo", "headerName": "Saldo", "type": "numericColumn", "flex": 1, "cellStyle": {"fontWeight": "bold"}}
                    ],
                    rowData=[],
                    className="ag-theme-alpine",
                    style={"height": 400},
                    defaultColDef={"resizable": True, "sortable": True, "filter": True}
                )
            ])
        ], className="mb-4 shadow-sm"),
        
        # Gráfico de evolución
        html.H5("📈 Evolución de Stock", className="mb-3"),
        
        dbc.Card([
            dbc.CardBody([
                dcc.Graph(id='inv-chart-evolucion')
            ])
        ], className="shadow-sm")
    ])


@callback(
    Output('inv-kpis', 'children'),
    Input('inv-producto', 'value')
)
def update_product_kpis(producto_id):
    """Actualiza los KPIs del producto seleccionado"""
    if not producto_id:
        return html.Div()
    
    info = db.obtener_info_producto(producto_id)
    
    return dbc.Row([
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H6("Stock Actual", className="text-muted"),
            html.H3(f"{info['stock_actual']:.0f} un.")
        ])]), width=3),
        
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H6("Valor Total", className="text-muted"),
            html.H3(f"S/ {info['valor_total']:,.2f}")
        ])]), width=3),
        
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H6("Costo Promedio", className="text-muted"),
            html.H3(f"S/ {info['costo_promedio']:,.2f}")
        ])]), width=3),
        
        dbc.Col(dbc.Card([dbc.CardBody([
            html.H6("Última Compra", className="text-muted"),
            html.H5(info['ultima_compra'])
        ])]), width=3)
    ])


@callback(
    [Output('inv-kardex-table', 'rowData'),
     Output('inv-chart-evolucion', 'figure')],
    [Input('inv-producto', 'value'),
     Input('global-date-range', 'start_date'),
     Input('global-date-range', 'end_date'),
     Input('theme-store', 'data')]
)
def update_kardex(producto_id, start_date, end_date, theme):
    """Actualiza el kardex y el gráfico usando filtro global"""
    if not producto_id:
        return [], go.Figure()
    
    if not start_date or not end_date:
        # Fallback date
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
    
    # Obtener kardex
    try:
        df_kardex = db.obtener_kardex_producto(producto_id, start_date, end_date)
    except Exception as e:
        print(f"Error fetching kardex: {e}")
        return [], go.Figure()
        
    # Preparar datos para la tabla
    kardex_data = df_kardex.to_dict('records')
    
    # Crear gráfico
    template = 'plotly_dark' if theme == 'dark' else 'plotly'
    
    fig = go.Figure()
    if not df_kardex.empty:
        fig.add_trace(go.Scatter(
            x=df_kardex['Fecha'],
            y=df_kardex['Saldo'],
            mode='lines+markers',
            name='Stock',
            line=dict(color='#1E3A8A', width=2),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        template=template,
        xaxis_title="Fecha",
        yaxis_title="Unidades en Stock",
        hovermode='x unified',
        height=350,
        margin=dict(t=20, b=20, l=20, r=20)
    )
    
    return kardex_data, fig
