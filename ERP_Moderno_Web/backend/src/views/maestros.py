import streamlit as st
import pandas as pd
import src.backend as db
from src.module_guides import render_maestros_guide

class MaestrosView:
    def render(self):
        st.markdown('<p class="main-header">Gestión de Datos</p>', unsafe_allow_html=True)
        
        tab_prov, tab_prod, tab_cat, tab_masivo, tab_guia = st.tabs(["👥 Proveedores", "📦 Productos", "🏷️ Categorías", "📤 Carga Masiva", "📖 Guía"])
        
        with tab_guia:
            render_maestros_guide()
        
        
        with tab_prov:
            st.subheader("Nuevo Proveedor")
            c1, c2 = st.columns(2)
            kp_ruc = c1.text_input("RUC/DNI", key="m_ruc")
            kp_rs = c2.text_input("Razón Social", key="m_rs")
            kp_dir = st.text_input("Dirección", key="m_dir")
            
            c3, c4 = st.columns(2)
            kp_tel = c3.text_input("Teléfono", key="m_tel")
            kp_email = c4.text_input("Email", key="m_email")
            
            if st.button("Guardar Proveedor", key="btn_save_prov"):
                if kp_ruc and kp_rs:
                    # Pass inputs to backend (ignoring contacto as DB doesn't have it)
                    ok, msg = db.crear_proveedor(kp_ruc, kp_rs, kp_dir, kp_tel, kp_email, "")
                    if ok: st.success(msg)
                    else: st.error(msg)
                else:
                    st.warning("Datos incompletos (RUC y Razón Social obligatorios)")
            st.divider()
            
            # Grid Completo
            df_prov = db.obtener_proveedores() # Ensure backend returns all cols
            if not df_prov.empty:
                # Backend query should be improved to return all columns, for now assume standard
                st.dataframe(
                    df_prov, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "ruc_dni": "RUC/DNI",
                        "razon_social": "Razón Social",
                        "direccion": "Dirección",
                        "telefono": "Teléfono",
                        "email": "Email",
                        "categoria": "Categoría"
                    }
                )
            else:
                st.info("No hay proveedores registrados.")

        with tab_prod:
            st.subheader("Nuevo Producto")
            c1, c2, c3 = st.columns(3)
            with c1: kd_sku = st.text_input("SKU / Código", key="m_sku")
            with c2: kd_nom = st.text_input("Nombre", key="m_nom")
            with c3: 
                cats = db.obtener_categorias()
                lista_cats = dict(zip(cats['nombre'], cats['id'])) if not cats.empty else {}
                kd_cat = st.selectbox("Categoría", list(lista_cats.keys()), key="m_cat")
            
            c4, c5 = st.columns(2)
            with c4: kd_um = st.selectbox("Unidad Medida", ["UND", "KG", "LITRO", "METRO", "CAJA", "LATE", "BOLSA"], key="m_um")
            with c5: kd_stock_min = st.number_input("Stock Mínimo", min_value=0.0, value=0.0, step=0.01, key="m_stock_min", help="Nivel mínimo de stock para alertas")
                
            if st.button("Guardar Producto", key="btn_save_prod"):
                if kd_nom and kd_cat:
                    cat_id = lista_cats[kd_cat]
                    ok, msg, pid = db.crear_producto(kd_sku, kd_nom, kd_um, cat_id, kd_stock_min)
                    if ok: 
                        st.success(msg)
                        # Limpiar formulario
                        for key in list(st.session_state.keys()):
                            if key.startswith('m_'):
                                del st.session_state[key]
                        st.rerun()
                    else: st.error(msg)
                else:
                    st.warning("Nombre y Categoría obligatorios")
            st.divider()
            
            df_prods_list = db.obtener_productos_extendido()
            if not df_prods_list.empty:
                df_prods_list.index = df_prods_list.index + 1
            st.dataframe(df_prods_list, use_container_width=True, hide_index=True)
            
            st.divider()
            st.markdown("#### 🗑️ Gestión de Eliminación")
            
            # Selectbox for deletion
            if not df_prods_list.empty:
                # Rebuild map as index was shifted
                df_prods_list = db.obtener_productos_extendido() # Get fresh ID
                opc_elim = df_prods_list.apply(lambda x: f"{x['codigo_sku']} | {x['nombre']}", axis=1).tolist()
                map_elim = dict(zip(opc_elim, df_prods_list['id']))
                
                c_del1, c_del2 = st.columns([3, 1])
                sel_del = c_del1.selectbox("Seleccionar Producto a Eliminar", opc_elim, key="del_prod_sel")
                
                if c_del2.button("Eliminar 🗑️", type="primary", key="btn_del_prod"):
                    pid_del = map_elim[sel_del]
                    ok, msg = db.eliminar_producto(pid_del)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.info("No hay productos para eliminar.")

        with tab_cat:
            st.subheader("Nueva Categoría")
            kc_nom = st.text_input("Nombre Categoría", key="m_cat_nom")
            if st.button("Guardar Categoría", key="btn_save_cat"):
                if kc_nom:
                    ok, msg = db.crear_categoria(kc_nom)
                    if ok: 
                        st.success(msg)
                        if 'm_cat_nom' in st.session_state:
                            del st.session_state['m_cat_nom']
                        st.rerun()
                    else: st.error(msg)
            st.divider()
            
            df_cats = db.obtener_categorias()
            if not df_cats.empty:
                df_cats.index = df_cats.index + 1
            st.dataframe(df_cats, use_container_width=True, hide_index=True)
            
        with tab_masivo:
            st.subheader("Carga Masiva (Excel)")
            
            opcion_carga = st.radio("Seleccionar Tipo de Carga", ["Productos", "Proveedores", "Compras (Próximamente)"], horizontal=True)
            
            if opcion_carga == "Compras (Próximamente)":
                st.info("🚧 Módulo de carga masiva de compras detalladas en construcción.")
                st.stop()

            # Generar Templates
            if opcion_carga == "Productos":
                st.markdown("##### 1. Descargar Plantilla")
                df_template_prod = pd.DataFrame(columns=["sku", "nombre", "categoria", "unidad_medida", "precio_compra", "precio_venta", "stock_minimo"])
                st.download_button(
                    label="📥 Descargar Plantilla Productos",
                    data=to_excel(df_template_prod),
                    file_name="plantilla_productos.xlsx"
                )
                
                st.markdown("##### 2. Subir Archivo")
                st.caption("Columnas requeridas: `sku`, `nombre`, `categoria` (texto), `unidad_medida`, `precio_compra`, `precio_venta`, `stock_minimo` (opcional)")
                uploaded_file = st.file_uploader("Seleccionar Excel Productos", type=["xlsx"], key="up_prod")
                
                if uploaded_file and st.button("Procesar Productos"):
                    procesar_carga_productos(uploaded_file, db)
                    
            elif opcion_carga == "Proveedores":
                st.markdown("##### 1. Descargar Plantilla")
                df_template_prov = pd.DataFrame(columns=["ruc_dni", "razon_social", "adireccion", "telefono", "email", "categoria"])
                st.download_button(
                    label="📥 Descargar Plantilla Proveedores",
                    data=to_excel(df_template_prov),
                    file_name="plantilla_proveedores.xlsx"
                )
                
                st.markdown("##### 2. Subir Archivo")
                st.caption("Columnas requeridas: `ruc_dni`, `razon_social`, `direccion`, `telefono`, `email`")
                uploaded_file = st.file_uploader("Seleccionar Excel Proveedores", type=["xlsx"], key="up_prov")
                
                if uploaded_file and st.button("Procesar Proveedores"):
                    procesar_carga_proveedores(uploaded_file, db)

def to_excel(df):
    import io
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

def procesar_carga_productos(uploaded_file, db):
    try:
        df = pd.read_excel(uploaded_file)
        # Normalizar columnas
        df.columns = [c.lower().strip() for c in df.columns]
        
        required = ['nombre', 'categoria']
        if not all(col in df.columns for col in required):
            st.error(f"Faltan columnas requeridas: {required}")
            return

        progres_bar = st.progress(0)
        log = []
        
        cats_cache = db.obtener_categorias()
        map_cats = dict(zip(cats_cache['nombre'].str.upper(), cats_cache['id'])) if not cats_cache.empty else {}
        
        for index, row in df.iterrows():
            cat_str = str(row.get('categoria', 'General')).upper()
            cat_id = map_cats.get(cat_str)
            
            # Si categoria no existe, crearla al vuelo? Mejor default 1 o error.
            if not cat_id:
                # Intentar crear o asignar default
                ok, _, new_id = db.crear_categoria(row.get('categoria', 'General'))
                if ok: 
                    cat_id = new_id
                    map_cats[cat_str] = new_id
                else:
                    cat_id = 1 # Fallback

            sku = str(row.get('sku', ''))
            if sku == 'nan': sku = None
            
            stock_min = float(row.get('stock_minimo', 0)) if pd.notna(row.get('stock_minimo')) else 0
            
            ok, msg, pid = db.crear_producto(
                sku, 
                row['nombre'], 
                row.get('unidad_medida', 'UND'), 
                cat_id,
                stock_min
            )
            # Update prices if provided
            if ok and pid:
                p_compra = float(row.get('precio_compra', 0)) if pd.notna(row.get('precio_compra')) else 0
                p_venta = float(row.get('precio_venta', 0)) if pd.notna(row.get('precio_venta')) else 0
                
                # Update prices logic would go here if backend supported specific update function
                # For now, create product is enough. Backfill prices later if needed.
                pass

            status = "✅" if ok else "❌"
            log.append(f"{status} {row['nombre']}: {msg}")
            progres_bar.progress((index + 1) / len(df))
            
        st.success("Proceso terminado")
        with st.expander("Ver Log de Carga"):
            st.code("\n".join(log))
            
    except Exception as e:
        st.error(f"Error procesando archivo: {e}")

def procesar_carga_proveedores(uploaded_file, db):
    try:
        df = pd.read_excel(uploaded_file)
        df.columns = [c.lower().strip() for c in df.columns]
        
        required = ['ruc_dni', 'razon_social']
        if not all(col in df.columns for col in required):
            st.error(f"Faltan columnas requeridas: {required}")
            return

        progres_bar = st.progress(0)
        log = []
        
        for index, row in df.iterrows():
            ruc = str(row['ruc_dni'])
            rs = str(row['razon_social'])
            
            ok, msg = db.crear_proveedor(
                ruc, 
                rs, 
                str(row.get('direccion', '')), 
                str(row.get('telefono', '')), 
                str(row.get('email', '')), 
                str(row.get('categoria', ''))
            )
            
            status = "✅" if ok else "❌"
            log.append(f"{status} {rs}: {msg}")
            progres_bar.progress((index + 1) / len(df))
            
        st.success("Proceso terminado")
        with st.expander("Ver Log de Carga"):
            st.code("\n".join(log))

    except Exception as e:
        st.error(f"Error procesando archivo: {e}")
