import streamlit as st
from datetime import date
import pandas as pd
import src.backend as db
from src.theme_manager import get_theme_css

# Import Views
from src.views.dashboard import DashboardView
from src.views.maestros import MaestrosView
from src.views.aprovisionamiento import AprovisionamientoView
from src.views.compras import ComprasView
from src.views.salidas import SalidasView
from src.views.inventario import InventarioView
from src.views.configuracion import ConfiguracionView
from src.views.movimientos import MovimientosView

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="ERP Lite - Gestión Comercial", layout="wide", page_icon="🏢")

# --- GESTIÓN DE ESTADO (SESSION STATE) ---
if 'theme_dark' not in st.session_state:
    st.session_state.theme_dark = False 

# --- APLICAR TEMA (CLEAN LIGHT) ---
st.markdown(get_theme_css(), unsafe_allow_html=True)

# --- SIDEBAR & NAVEGACIÓN ---
with st.sidebar:
    # Obtener configuración de empresa
    nombre_empresa = db.obtener_configuracion('nombre_empresa', 'ERP Lite')
    logo_path = db.obtener_configuracion('logo_path', '')
    
    import os
    if logo_path and os.path.exists(logo_path):
        # Centrar logo más pequeño
        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2:
            st.image(logo_path, width=120)
        st.markdown(f"<h3 style='text-align: center; color: #2563EB; margin-top: -10px;'>{nombre_empresa}</h3>", unsafe_allow_html=True)
    else:
        st.title(f"🏢 {nombre_empresa}")
    
    menu = st.radio("Navegación", [
        "Inicio", 
        "🚛 Aprovisionamiento",
        "🛒 Compras (Facturas)", 
        "📤 Salidas / Servicios",
        "🔄 Logística / Movimientos",
        "📦 Inventario", 
        "⚙️ Gestión de Datos",
        "🔧 Configuración"
    ])
    
    st.info("Versión: 4.0 (Refactorizada)")
    st.divider()
    
    # Filtro de Fechas (Global para Dashboard)
    if menu == "Inicio":
        st.markdown("### 📅 Periodo de Análisis")
        
        # Filtros Rápidos
        col_q1, col_q2, col_q3 = st.columns(3)
        if col_q1.button("Mes", use_container_width=True):
            st.session_state['f_ini'] = date.today().replace(day=1)
            st.session_state['f_fin'] = date.today()
            st.rerun()
            
        if col_q2.button("Año", use_container_width=True):
            st.session_state['f_ini'] = date.today().replace(month=1, day=1)
            st.session_state['f_fin'] = date.today()
            st.rerun()
            
        if col_q3.button("Todo", use_container_width=True):
            st.session_state['f_ini'] = date.today() - pd.Timedelta(days=365*2)
            st.session_state['f_fin'] = date.today()
            st.rerun()

        # Defaults
        if 'f_ini' not in st.session_state: 
            st.session_state['f_ini'] = date.today() - pd.Timedelta(days=30)
        if 'f_fin' not in st.session_state: 
            st.session_state['f_fin'] = date.today()
        
        # Selectores
        start_date = st.date_input("Desde", st.session_state['f_ini'], key='d_from')
        end_date = st.date_input("Hasta", st.session_state['f_fin'], key='d_to')
        
        # Sync
        if start_date != st.session_state['f_ini']: st.session_state['f_ini'] = start_date
        if end_date != st.session_state['f_fin']: st.session_state['f_fin'] = end_date

        if start_date > end_date:
            st.error("⚠️ Fecha Inicio > Fecha Fin")

# --- ENRUTAMIENTO DE VISTAS ---

if menu == "Inicio":
    view = DashboardView()
    # Dashboard necesita fechas
    f_start = st.session_state.get('f_ini', date.today())
    f_end = st.session_state.get('f_fin', date.today())
    view.render(f_start, f_end)

elif menu == "🚛 Aprovisionamiento":
    view = AprovisionamientoView()
    view.render()

elif menu == "🛒 Compras (Facturas)":
    view = ComprasView()
    view.render()

elif menu == "📤 Salidas / Servicios":
    view = SalidasView()
    view.render()

elif menu == "🔄 Logística / Movimientos":
    view = MovimientosView()
    view.render()

elif menu == "📦 Inventario":
    view = InventarioView()
    view.render()

elif menu == "⚙️ Gestión de Datos":
    view = MaestrosView()
    view.render()

elif menu == "🔧 Configuración":
    view = ConfiguracionView()
    view.render()
