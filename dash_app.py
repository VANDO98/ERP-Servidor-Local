"""
Sistema ERP con Dash - Aplicación Principal
Migrado desde Streamlit para mejor control de temas y tablas editables
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from src.layouts import sidebar, dashboard, aprovisionamiento, compras, salidas, inventario, maestros

# Inicializar app con tema Bootstrap
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME
    ],
    suppress_callback_exceptions=True,
    title="Sistema ERP - Gestión Básica"
)

server = app.server

# Layout principal con ThemeSwitchAIO
app.layout = dbc.Container([
    dcc.Store(id='theme-store', data='light'),
    dcc.Location(id='url', refresh=False),
    
    dbc.Row([
        # Sidebar
        dbc.Col(
            sidebar.create_layout(),
            width=2,
            className="vh-100 bg-light border-end",
            style={'position': 'fixed', 'left': 0, 'top': 0, 'overflow-y': 'auto'}
        ),
        
        # Content Area
        dbc.Col(
            html.Div(id='page-content', className="p-4"),
            width=10,
            style={'margin-left': '16.666667%'}  # offset for fixed sidebar
        )
    ], className="g-0")
], fluid=True, id='main-container', className="p-0")


# Callback para routing de páginas
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/' or pathname == '/dashboard':
        return dashboard.create_layout()
    elif pathname == '/aprovisionamiento':
        return aprovisionamiento.create_layout()
    elif pathname == '/compras':
        return compras.create_layout()
    elif pathname == '/salidas':
        return salidas.create_layout()
    elif pathname == '/inventario':
        return inventario.create_layout()
    elif pathname == '/maestros':
        return maestros.create_layout()
    else:
        return html.Div([
            html.H2("404 - Página no encontrada"),
            dcc.Link("Volver al Dashboard", href="/")
        ])


# Callback para cambio de tema
@app.callback(
    [Output('main-container', 'className'),
     Output('theme-store', 'data')],
    Input('theme-toggle', 'value'),
    prevent_initial_call=False
)
def switch_theme(theme_value):
    """Cambia entre tema claro y oscuro"""
    if theme_value:  # True = Dark Mode
        return "p-0 bg-dark text-light", "dark"
    else:  # False = Light Mode
        return "p-0 bg-light text-dark", "light"


if __name__ == '__main__':
    print("🚀 Iniciando servidor Dash en http://localhost:8050")
    app.run_server(debug=True, port=8050, host='0.0.0.0')
