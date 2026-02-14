"""
Theme Manager - Gestión de Estilos Visuales (Clean Light Theme)
Diseño minimalista y profesional.
"""

def get_theme_css() -> str:
    """Retorna el CSS global del aplicativo"""
    return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

            :root {
                --primary: #2563EB;
                --primary-hover: #1D4ED8;
                --bg-body: #F1F5F9;
                --bg-card: #FFFFFF;
                --text-main: #0F172A;
                --text-secondary: #64748B;
                --border-color: #E2E8F0;
                
                --success: #10B981;
                --warning: #F59E0B;
                --danger: #EF4444;
            }

            /* Global Settings */
            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif;
                color: var(--text-main);
            }

            /* Main Container Background */
            .stApp {
                background-color: var(--bg-body) !important;
            }
            
            /* Sidebar */
            section[data-testid="stSidebar"] {
                background-color: #FFFFFF !important;
                border-right: 1px solid var(--border-color);
            }
            
            /* Typography */
            h1, h2, h3 {
                color: var(--text-main) !important;
                font-weight: 600 !important;
            }
            h1 { font-size: 2rem !important; }
            h2 { font-size: 1.5rem !important; }
            h3 { font-size: 1.25rem !important; }
            
            p, label, span, div {
                color: var(--text-main);
            }
            
            /* Custom Main Header */
            .main-header {
                font-size: 1.75rem;
                font-weight: 700;
                color: var(--primary) !important;
                margin-bottom: 1rem;
                border-bottom: 2px solid var(--border-color);
                padding-bottom: 0.5rem;
            }

            /* Cards / Containers (Metrics) */
            div[data-testid="stMetric"] {
                background-color: var(--bg-card);
                border: 1px solid var(--border-color);
                padding: 0.75rem !important;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }
            div[data-testid="stMetric"] label {
                color: var(--text-secondary) !important;
                font-size: 0.8rem !important;
                white-space: nowrap !important;
            }
            div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
                color: var(--primary) !important;
                font-weight: 700 !important;
                font-size: 1.25rem !important;
            }

            /* Inputs */
            .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
                background-color: var(--bg-card) !important;
                color: var(--text-main) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: 6px !important;
            }
            .stTextInput input:focus, .stNumberInput input:focus {
                border-color: var(--primary) !important;
                box-shadow: 0 0 0 1px var(--primary) !important;
            }

            /* Buttons */
            .stButton button {
                background-color: var(--primary) !important;
                color: #FFFFFF !important; #2563EB
                border: none !important;
                font-weight: 500 !important;
                border-radius: 6px !important;
                transition: all 0.2s;
            }
            .stButton button:hover {
                background-color: var(--primary-hover) !important;
                box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
            }
            .stButton button:active {
                transform: translateY(1px);
            }

            /* Dataframes */
            div[data-testid="stDataFrame"] {
                background-color: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 8px;
            }
            
            /* Tabs */
            .stTabs [data-baseweb="tab-list"] {
                gap: 2px;
            }
            .stTabs [data-baseweb="tab"] {
                background-color: transparent !important;
                border-radius: 4px;
                color: var(--text-secondary);
            }
            .stTabs [aria-selected="true"] {
                background-color: #EFF6FF !important; /* Blue 50 */
                color: var(--primary) !important;
                font-weight: 600 !important;
            }

            /* Expander */
            .streamlit-expanderHeader {
                background-color: var(--bg-card) !important;
                color: var(--text-main) !important;
                border: 1px solid var(--border-color);
                border-radius: 6px;
            }


            /* --- CALENDAR CUSTOMIZATION (Clean Light) --- */
            /* Removed Dark Override to match system theme and fix readability */
            div[data-baseweb="calendar"] {
                background-color: var(--bg-card) !important;
                border: 1px solid var(--border-color) !important;
            }
             
            /* Selectbox/Input Icons */
            div[data-baseweb="select"] svg, div[data-baseweb="input"] svg {
                fill: var(--text-secondary) !important;
            }

            
        </style>
    """

def get_chart_text_color() -> str:
    """Color de texto para gráficos (Always Dark)"""
    return "#334155" # Slate 700
