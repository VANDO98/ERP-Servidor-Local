import streamlit as st
import pandas as pd
from datetime import date
import src.backend as db

class SalidasView:
    def render(self):
        st.markdown('<p class="main-header">Registro de Salidas (Materiales & Servicios)</p>', unsafe_allow_html=True)
        
        tab_reg, tab_hist, tab_det = st.tabs(["📝 Registrar Salida", "📜 Historial (Resumen)", "🔍 Historial (Detallado)"])
        
        with tab_reg:
            st.info("ℹ️ Registra aquí el consumo de materiales para Servicios, Ventas Directas o Merma.")
            
            # 1. Cabecera
            c1, c2, c3 = st.columns(3)
            fecha_salida = c1.date_input("Fecha", date.today(), key="s_fecha")
            tipo_mov = c2.selectbox("Tipo Movimiento", ["SERVICIO", "VENTA DIRECTA", "CONSUMO INTERNO", "MERMA"], key="s_tipo")
            destino = c3.text_input("Cliente / Proyecto / Destino", key="s_dest")
            obs = st.text_area("Observaciones", key="s_obs")
            
            st.divider()
            
            # 2. Detalle (Grid)
            df_prods = db.obtener_productos_extendido()
            
            # Obtener Almacenes
            df_alm = db.obtener_almacenes()
            if not df_alm.empty:
                almacenes_opts = df_alm['nombre'].tolist()
                mapa_almacenes = dict(zip(df_alm['nombre'], df_alm['id']))
            else:
                almacenes_opts = ["Almacén Principal"]
                mapa_almacenes = {"Almacén Principal": 1}

            if not df_prods.empty:
                df_prods['label'] = df_prods.apply(lambda x: f"{x['codigo_sku']} | {x['nombre']} (Stock: {x['stock_actual']:.2f})", axis=1)
                prod_map = df_prods.set_index('label')[['id', 'unidad_medida', 'stock_actual', 'precio_venta']].to_dict('index')
                opciones_prods = df_prods['label'].tolist()
            else:
                opciones_prods = []
                prod_map = {}

            if 'df_salidas' not in st.session_state:
                st.session_state.df_salidas = pd.DataFrame(columns=["Producto", "U.M.", "Cantidad", "Almacen Origen"])

            col_config = {
                "Producto": st.column_config.SelectboxColumn("Producto", options=opciones_prods, width="large", required=True),
                "U.M.": st.column_config.TextColumn("U.M.", width="small", disabled=True),
                "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.01, step=0.01, width="small"),
                "Almacen Origen": st.column_config.SelectboxColumn("Almacén", options=almacenes_opts, required=True, default=almacenes_opts[0], width="medium") 
            }
            
            if 'key_salidas' not in st.session_state:
                st.session_state.key_salidas = 0

            # Sanitize columns
            valid_cols = ["Producto", "U.M.", "Cantidad", "Almacen Origen"]
            
            if list(st.session_state.df_salidas.columns) != valid_cols:
                clean_data = {col: st.session_state.df_salidas[col] for col in valid_cols if col in st.session_state.df_salidas}
                st.session_state.df_salidas = pd.DataFrame(clean_data, columns=valid_cols)
            
            st.session_state.df_salidas.reset_index(drop=True, inplace=True)

            edited_df = st.data_editor(
                st.session_state.df_salidas,
                column_config=col_config,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key=f"editor_salidas_{st.session_state.key_salidas}"
            )

            # Logic to autofill U.M.
            if not edited_df.equals(st.session_state.df_salidas):
                need_rerun = False
                for i, row in edited_df.iterrows():
                    if row["Producto"]:
                        pid = prod_map.get(row["Producto"], {}).get('id')
                        if pid:
                           # Auto-fill U.M. (Robust)
                           current_um = str(row.get("U.M.", "")).strip()
                           target_um = str(prod_map[row["Producto"]].get('unidad_medida', 'UND')).strip()
                           if not target_um or target_um == 'nan': target_um = 'UND'
                           
                           if current_um != target_um:
                               edited_df.at[i, "U.M."] = target_um
                               need_rerun = True
                
                if need_rerun:
                    st.session_state.df_salidas = edited_df
                    st.session_state.key_salidas += 1
                    st.rerun()
                else:
                    st.session_state.df_salidas = edited_df
            
            if st.button("📤 REGISTRAR SALIDA", type="primary"):
                if edited_df.empty:
                    st.error("⚠️ Detalle vacío.")
                else:
                    detalles = []
                    valid = True
                    for _, row in edited_df.iterrows():
                        if row["Producto"] and row["Cantidad"] > 0:
                            pid = prod_map[row["Producto"]]['id']
                            current_stock = prod_map[row["Producto"]]['stock_actual']
                            if row["Cantidad"] > current_stock:
                                st.error(f"⛔ Stock insuficiente para {row['Producto']}. Tienes {current_stock}, intentas sacar {row['Cantidad']}.")
                                valid = False
                                break
                            
                            # Lookup ID from map
                            alm_name = row["Almacen Origen"]
                            alm_id = mapa_almacenes.get(alm_name, 1)
                            
                            detalles.append({
                                "pid": pid,
                                "cantidad": row["Cantidad"],
                                "almacen_id": alm_id 
                            })
                    
                    if valid and detalles:
                        cab = {
                            "fecha": fecha_salida,
                            "tipo": tipo_mov, 
                            "destino": destino,
                            "obs": obs
                        }
                        ok, msg = db.registrar_salida(cab, detalles)
                        if ok:
                            st.success(msg)
                            st.balloons()
                            
                            # Limpiar detalle y cabecera
                            st.session_state.df_salidas = pd.DataFrame(columns=["Producto", "U.M.", "Cantidad", "Almacen Origen"])
                            for key in list(st.session_state.keys()):
                                if key.startswith('s_'):
                                    del st.session_state[key]
                            
                            st.rerun()
                        else:
                            st.error(msg)
        
        with tab_hist:
            st.subheader("Historial de Salidas (Resumen)")
            df_hist = db.obtener_historial_salidas()
            if not df_hist.empty:
                st.dataframe(df_hist, use_container_width=True, hide_index=True)
            else:
                st.info("No hay salidas registradas aún.")
        
        with tab_det:
            st.subheader("Historial de Salidas (Detallado)")
            df_det = db.obtener_historial_salidas_detallado()
            if not df_det.empty:
                st.dataframe(df_det, use_container_width=True, hide_index=True)
            else:
                st.info("No hay salidas registradas aún.")
