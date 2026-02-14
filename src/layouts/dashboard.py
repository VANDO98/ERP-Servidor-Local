"""
Dashboard Layout - Vista principal con KPIs y Gráficos
"""

from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from src import dashboard_backend as db
from datetime import date, timedelta
import pandas as pd

def create_layout():
    """Crea el layout del dashboard"""
    return html.Div([
        html.H2("📊 Dashboard General", className="mb-4"),
        
        # NOTE: Date filter is now in Sidebar (global-date-range)
        
        # KPIs
        html.Div(id='dashboard-kpis', className="mb-4"),
        
        # Gráficos
        dbc.Row([
            # Top Proveedores (Donut)
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🏆 Top Proveedores"),
                    dbc.CardBody(dcc.Graph(id='chart-top-proveedores', style={'height': '350px'}))
                ], className="shadow-sm h-100")
            ], width=6),
            
            # Gasto por Categoría (Barra Horizontal)
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("🍩 Gasto por Categoría"),
                    dbc.CardBody(dcc.Graph(id='chart-gastos-categoria', style={'height': '350px'}))
                ], className="shadow-sm h-100")
            ], width=6),
        ], className="mb-4"),
        
        # Evolución de Compras (Columnas)
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📈 Evolución de Compras"),
                    dbc.CardBody(dcc.Graph(id='chart-evolucion-compras', style={'height': '300px'}))
                ], className="shadow-sm")
            ], width=12)
        ])
    ])


@callback(
    [Output('dashboard-kpis', 'children'),
     Output('chart-top-proveedores', 'figure'),
     Output('chart-gastos-categoria', 'figure'),
     Output('chart-evolucion-compras', 'figure')],
    [Input('global-date-range', 'start_date'),
     Input('global-date-range', 'end_date')]
)
def update_dashboard(start_date, end_date):
    if not start_date or not end_date:
        # Default fallback if sidebar not ready (should not happen usually)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
    # 1. KPIs
    kpis = db.obtener_kpis_dashboard(start_date, end_date)
    
    kpi_cards = dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("💰 Compras Totales", className="card-subtitle text-muted"),
                html.H3(f"S/ {kpis['compras_monto']:,.2f}", className="card-title text-primary")
            ])
        ], className="shadow-sm"), width=3),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("📦 Valor Inventario (FIFO)", className="card-subtitle text-muted"),
                html.H3(f"S/ {kpis['valor_inventario']:,.2f}", className="card-title text-success")
            ])
        ], className="shadow-sm"), width=3),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("📝 Facturas", className="card-subtitle text-muted"),
                html.H3(f"{kpis['compras_docs']}", className="card-title text-info")
            ])
        ], className="shadow-sm"), width=3),
        
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H6("💵 T.C. Referencial", className="card-subtitle text-muted"),
                html.H3(f"S/ {kpis['tc']:.3f}", className="card-title text-warning")
            ])
        ], className="shadow-sm"), width=3),
    ])
    
    # 2. Charts
    
    # Top Proveedores (Donut)
    df_top = db.obtener_top_proveedores(start_date, end_date)
    fig_top = go.Figure()
    if not df_top.empty:
        fig_top = px.pie(df_top, values='Monto', names='Proveedor', hole=0.4)
        fig_top.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    else:
        fig_top.add_annotation(text="Sin datos", showarrow=False)

    # Gasto por Categoría (Barra Horizontal)
    df_cat = db.obtener_gastos_por_categoria(start_date, end_date)
    fig_cat = go.Figure()
    if not df_cat.empty:
        fig_cat = px.bar(df_cat, x='Monto', y='Categoria', orientation='h', text_auto=',.2f')
        fig_cat.update_layout(margin=dict(t=0, b=0, l=0, r=0), yaxis={'categoryorder':'total ascending'})
    else:
        fig_cat.add_annotation(text="Sin datos", showarrow=False)
        
    # Evolución (Columnas)
    df_evol = db.obtener_evolucion_compras(start_date, end_date)
    fig_evol = go.Figure()
    if not df_evol.empty:
        fig_evol = px.bar(df_evol, x='Fecha', y='Monto', text_auto=',.2f')
        fig_evol.update_layout(margin=dict(t=20, b=20, l=20, r=20), xaxis_title=None, yaxis_title="Monto (S/)")
    else:
        fig_evol.add_annotation(text="Sin datos", showarrow=False)

    return kpi_cards, fig_top, fig_cat, fig_evol
