import streamlit as st
import pandas as pd
from datetime import date
import src.backend as db

class MovimientosView:
    def render(self):
        st.markdown('<p class="main-header">Logística Interna & Traslados</p>', unsafe_allow_html=True)
        
        tab_reg, tab_hist, tab_bus = st.tabs(["🚛 Registrar Traslado", "📜 Historial de Traslados", "🔎 Buscador de Stock"])
        
        # --- TAB 1: REGISTRAR TRASLADO ---
        with tab_reg:
            st.info("ℹ️ Mueve mercadería entre almacenes. El costo se calculará automáticamente (FIFO).")
            
            # Cabecera

            # Obtener Almacenes
            df_alm = db.obtener_almacenes()
            if not df_alm.empty:
                # Deduplicate based on ID just in case, though DB should be clean now
                df_alm = df_alm.drop_duplicates(subset=['id'])
                
                # Sort by name
                df_alm = df_alm.sort_values('nombre')
                
                almacenes_opts = df_alm['nombre'].tolist()
                mapa_almacenes = dict(zip(df_alm['nombre'], df_alm['id']))
            else:
                st.error("No hay almacenes registrados.")
                return

            c1, c2, c3 = st.columns(3)
            fecha = c1.date_input("Fecha Traslado", date.today(), key="t_fecha")

            # Default indices logic
            idx_origen = 0
            idx_destino = 1 if len(almacenes_opts) > 1 else 0

            origen_nombre = c2.selectbox("Almacén Origen", almacenes_opts, index=idx_origen, key="t_origen")
            destino_nombre = c3.selectbox("Almacén Destino", almacenes_opts, index=idx_destino, key="t_destino")
            
            obs = st.text_area("Observaciones", key="t_obs")

            st.divider()
            
            # Validacion Origen != Destino
            if origen_nombre == destino_nombre:
                st.warning("⚠️ El origen y destino no pueden ser el mismo.")
            
            # Grid de Productos
            # Cargar productos con stock específico del almacén origen seleccionado
            if origen_nombre:
                origen_id = mapa_almacenes[origen_nombre]
                df_prods = db.obtener_productos_con_stock_por_almacen(origen_id)
            else:
                df_prods = pd.DataFrame()
            
            if not df_prods.empty:
                # Format: SKU | Nombre | Global: X | Stock [Alm]: Y
                prods_labels = df_prods.apply(
                    lambda x: f"{x['codigo_sku']} | {x['nombre']} | Global: {x['stock_global']:.2f} | Stock Alm. {origen_nombre}: {x['stock_almacen']:.2f}", 
                    axis=1
                )
                df_prods['label'] = prods_labels
                prod_map = df_prods.set_index('label')[['id', 'unidad_medida', 'stock_almacen']].to_dict('index')
                opciones_prods = df_prods['label'].tolist()
            else:
                opciones_prods = []
                prod_map = {}

            if 'df_traslados' not in st.session_state:
                st.session_state.df_traslados = pd.DataFrame(columns=["Producto", "Cantidad", "U.M."])

            col_config = {
                "Producto": st.column_config.SelectboxColumn("Producto", options=opciones_prods, width="large", required=True),
                "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.01, step=0.01, width="small"),
                "U.M.": st.column_config.TextColumn("U.M.", disabled=True, width="small")
            }
            
            if 'key_traslados' not in st.session_state:
                st.session_state.key_traslados = 0

            # Reset Index to avoid phantom columns
            st.session_state.df_traslados.reset_index(drop=True, inplace=True)

            edited_df = st.data_editor(
                st.session_state.df_traslados,
                column_config=col_config,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key=f"editor_traslados_{st.session_state.key_traslados}"
            )
            
            # Auto-fill U.M. logic
            if not edited_df.equals(st.session_state.df_traslados):
                need_rerun = False
                for i, row in edited_df.iterrows():
                    if row["Producto"] and row["Producto"] in prod_map:
                        correct_um = prod_map[row["Producto"]]['unidad_medida']
                        if row.get("U.M.") != correct_um:
                            edited_df.at[i, "U.M."] = correct_um
                            need_rerun = True
                
                if need_rerun:
                    st.session_state.df_traslados = edited_df
                    st.session_state.key_traslados += 1
                    st.rerun()
                else:
                    st.session_state.df_traslados = edited_df
            
            if st.button("🚀 PROCESAR TRASLADO", type="primary"):
                if origen_nombre == destino_nombre:
                    st.error("⚠️ El origen y destino no pueden ser el mismo.")
                elif edited_df.empty:
                    st.error("⚠️ Lista de items vacía.")
                else:
                    detalles = []
                    valid = True
                    for i, row in edited_df.iterrows():
                        if row["Producto"] and row["Cantidad"] > 0:
                            if row["Producto"] in prod_map:
                                p_info = prod_map[row["Producto"]]
                                pid = p_info['id']
                                stock_disp = p_info.get('stock_almacen', 0)
                                
                                # Frontend Validation
                                if row["Cantidad"] > stock_disp:
                                    st.error(f"⛔ Stock insuficiente en línea {i+1}: {row['Producto']} (Solicitado: {row['Cantidad']} > Disp: {stock_disp})")
                                    valid = False
                                
                                detalles.append({
                                    "pid": pid,
                                    "cantidad": row["Cantidad"]
                                })
                    
                    if valid and detalles:
                        cab = {
                            "fecha": fecha,
                            "origen_id": mapa_almacenes[origen_nombre],
                            "destino_id": mapa_almacenes[destino_nombre],
                            "observaciones": obs
                        }
                        
                        ok, msg = db.registrar_traslado(cab, detalles)
                        if ok:
                            st.success(f"✅ {msg}")
                            st.balloons()
                            # Reset
                            st.session_state.df_traslados = pd.DataFrame(columns=["Producto", "Cantidad", "U.M."])
                            st.session_state.key_traslados += 1
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {msg}")

        # --- TAB 2: HISTORIAL ---
        with tab_hist:
            st.subheader("Historial de Movimientos")
            df_h = db.obtener_historial_traslados()
            # Ensure UMs column is shown and renamed if needed
            st.dataframe(df_h, use_container_width=True, hide_index=True)
            
        # --- TAB 3: BUSCADOR STOCK ---
        with tab_bus:
            st.subheader("🔍 Buscador de Stock por Almacén")
            
            # Filtro
            all_prods = db.obtener_productos()
            if not all_prods.empty:
                prod_opts = ["Todos"] + all_prods['nombre'].tolist()
                sel_prod = st.selectbox("Filtrar por Producto", prod_opts)
                
                pid_search = None
                if sel_prod != "Todos":
                    pid_search = int(all_prods[all_prods['nombre'] == sel_prod]['id'].values[0])
                
                df_stock = db.obtener_stock_por_almacen(pid_search)
                
                # Pivot for cleaner view if "Todos"
                if sel_prod == "Todos":
                    st.dataframe(df_stock, use_container_width=True, hide_index=True)
                else:
                    # Show metrics
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.dataframe(df_stock[['Almacen', 'Stock', 'UM']], use_container_width=True, hide_index=True)
                    with c2:
                        total = df_stock['Stock'].sum()
                        st.metric("Stock Global", f"{total:,.2f}")
            else:
                st.warning("No hay productos registrados.")
