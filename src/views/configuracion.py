import streamlit as st
import os
import shutil
from PIL import Image
import src.backend as db

class ConfiguracionView:
    def render(self):
        st.markdown('<p class="main-header">⚙️ Configuración del Sistema</p>', unsafe_allow_html=True)
        
        tab_empresa, tab_general, tab_sistema = st.tabs(["🏢 Información de Empresa", "💰 Configuración Financiera", "🔧 Sistema"])
        
        with tab_empresa:
            st.subheader("Información de la Empresa")
            
            # Obtener configuraciones actuales
            nombre_empresa = db.obtener_configuracion('nombre_empresa', 'Mi Empresa')
            logo_path = db.obtener_configuracion('logo_path', '')
            
            # Nombre de empresa
            nuevo_nombre = st.text_input("Nombre de la Empresa", value=nombre_empresa, key="cfg_nombre")
            
            st.divider()
            
            # Logo
            st.markdown("### Logo de la Empresa")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if logo_path and os.path.exists(logo_path):
                    try:
                        st.image(logo_path, caption="Logo actual", width=200)
                        if st.button("🗑️ Eliminar Logo"):
                            db.guardar_configuracion('logo_path', '')
                            st.success("Logo eliminado")
                            st.rerun()
                    except:
                        st.warning("No se pudo cargar el logo")
                else:
                    st.info("No hay logo configurado")
            
            with col2:
                uploaded_file = st.file_uploader(
                    "Subir nuevo logo",
                    type=['png', 'jpg', 'jpeg'],
                    help="Formatos: PNG, JPG, JPEG. Tamaño recomendado: 200x200px"
                )
                
                if uploaded_file:
                    # Crear directorio para logos si no existe
                    logo_dir = os.path.join("data", "logos")
                    os.makedirs(logo_dir, exist_ok=True)
                    
                    # Guardar archivo
                    logo_filename = f"logo_{uploaded_file.name}"
                    logo_save_path = os.path.join(logo_dir, logo_filename)
                    
                    with open(logo_save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Actualizar configuración
                    db.guardar_configuracion('logo_path', logo_save_path)
                    st.success(f"✅ Logo guardado: {logo_filename}")
                    st.rerun()
            
            st.divider()
            
            if st.button("💾 Guardar Información de Empresa", type="primary"):
                db.guardar_configuracion('nombre_empresa', nuevo_nombre)
                st.success("✅ Información guardada correctamente")
                st.rerun()
        
        with tab_general:
            st.subheader("Configuración Financiera")
            
            moneda = db.obtener_configuracion('moneda_principal', 'PEN')
            igv = db.obtener_configuracion('igv_default', '18')
            
            col1, col2 = st.columns(2)
            
            with col1:
                nueva_moneda = st.selectbox(
                    "Moneda Principal",
                    options=['PEN', 'USD'],
                    index=0 if moneda == 'PEN' else 1,
                    help="Moneda por defecto para reportes y visualizaciones"
                )
            
            with col2:
                nuevo_igv = st.number_input(
                    "Tasa de IGV (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(igv),
                    step=0.1,
                    help="Tasa de IGV por defecto para cálculos"
                )
            
            if st.button("💾 Guardar Configuración Financiera", type="primary"):
                db.guardar_configuracion('moneda_principal', nueva_moneda)
                db.guardar_configuracion('igv_default', str(nuevo_igv))
                st.success("✅ Configuración financiera guardada")
                st.rerun()
        
        with tab_sistema:
            st.subheader("Configuración del Sistema")
            
            almacen = db.obtener_configuracion('almacen_principal', 'Almacén Principal')
            
            nuevo_almacen = st.text_input(
                "Nombre del Almacén Principal",
                value=almacen,
                help="Nombre del almacén principal para operaciones"
            )
            
            st.divider()
            
            st.markdown("### Información del Sistema")
            st.info("""
            **Versión:** 1.0.0  
            **Base de Datos:** SQLite  
            **Framework:** Streamlit  
            """)
            
            if st.button("💾 Guardar Configuración del Sistema", type="primary"):
                db.guardar_configuracion('almacen_principal', nuevo_almacen)
                st.success("✅ Configuración del sistema guardada")
                st.rerun()
