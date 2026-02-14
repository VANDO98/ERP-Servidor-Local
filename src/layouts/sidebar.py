"""
Sidebar Component - Navegación principal y controles
"""

from dash import html, dcc, Input, Output, callback, ctx
import dash_bootstrap_components as dbc
from datetime import date, timedelta
import pandas as pd

def create_layout():
    """Crea el layout del sidebar con navegación y controles"""
    
    today = date.today()
    start_month = today.replace(day=1)
    
    return html.Div([
        # Header
        html.Div([
            html.H4("📊 ERP System", className="text-primary mb-0"),
            html.Small("Gestión Básica", className="text-muted")
        ], className="p-3 border-bottom"),
        
        # Navigation Menu
        html.Div([
            html.H6("NAVEGACIÓN", className="text-muted text-uppercase px-3 pt-3 pb-2", style={'fontSize': '0.75rem'}),
            
            dbc.Nav([
                dbc.NavLink([html.I(className="fas fa-chart-line me-2"), "Dashboard"], href="/dashboard", active="exact", className="text-dark"),
                dbc.NavLink([html.I(className="fas fa-truck me-2"), "Aprovisionamiento"], href="/aprovisionamiento", active="exact", className="text-dark"),
                dbc.NavLink([html.I(className="fas fa-shopping-cart me-2"), "Compras"], href="/compras", active="exact", className="text-dark"),
                dbc.NavLink([html.I(className="fas fa-box-open me-2"), "Salidas/Servicios"], href="/salidas", active="exact", className="text-dark"),
                dbc.NavLink([html.I(className="fas fa-warehouse me-2"), "Inventario"], href="/inventario", active="exact", className="text-dark"),
                dbc.NavLink([html.I(className="fas fa-cogs me-2"), "Maestros"], href="/maestros", active="exact", className="text-dark"),
            ], vertical=True, pills=True, className="px-2"),
        ]),
        
        # Divider
        html.Hr(className="my-3"),
        
        # Global Date Filter
        html.Div([
            html.H6("📅 PERIODO DE ANÁLISIS", className="text-muted text-uppercase px-3 pb-2", style={'fontSize': '0.75rem'}),
            
            # Presets
            html.Div([
                dbc.ButtonGroup([
                    dbc.Button("Mes", id="btn-mes", size="sm", outline=True, color="secondary"),
                    dbc.Button("Año", id="btn-anio", size="sm", outline=True, color="secondary"),
                    dbc.Button("Todo", id="btn-todo", size="sm", outline=True, color="secondary"),
                ], className="w-100 px-3 mb-2")
            ]),
            
            # Date Picker
            html.Div([
                dcc.DatePickerRange(
                    id='global-date-range',
                    start_date=start_month,
                    end_date=today,
                    display_format='DD/MM/YYYY',
                    className="w-100",
                    style={'fontSize': '0.8rem'}
                )
            ], className="px-3")
        ]),

        html.Hr(className="my-3"),
        
        # Theme Toggle
        html.Div([
            html.H6("🎨 TEMA VISUAL", className="text-muted text-uppercase px-3 pb-2", style={'fontSize': '0.75rem'}),
            html.Div([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Switch(
                            id="theme-toggle",
                            label="🌙 Modo Oscuro",
                            value=False,
                            className="mb-0"
                        )
                    ], className="p-2")
                ], className="shadow-sm mx-2")
            ])
        ]),
        
        # Version Info
        html.Div([
            html.Hr(className="my-3"),
            html.Small([
                html.I(className="fas fa-info-circle me-1"),
                "Versión 2.0 (Dash)"
            ], className="text-muted px-3")
        ], className="mt-auto")
        
    ], className="d-flex flex-column h-100")


# Callback para presets de fechas
@callback(
    [Output('global-date-range', 'start_date'),
     Output('global-date-range', 'end_date')],
    [Input('btn-mes', 'n_clicks'),
     Input('btn-anio', 'n_clicks'),
     Input('btn-todo', 'n_clicks')],
    prevent_initial_call=True
)
def update_dates(btn_mes, btn_anio, btn_todo):
    trigger = ctx.triggered_id
    today = date.today()
    
    if trigger == 'btn-mes':
        start = today.replace(day=1)
        return start, today
    elif trigger == 'btn-anio':
        start = today.replace(month=1, day=1)
        return start, today
    elif trigger == 'btn-todo':
        start = today - timedelta(days=365*2)
        return start, today
    
    return dash.no_update, dash.no_update
