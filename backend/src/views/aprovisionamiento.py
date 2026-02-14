import streamlit as st
import pandas as pd
from datetime import date, timedelta
import src.backend as db
from src.module_guides import render_aprovisionamiento_guide

class AprovisionamientoView:
    def render(self):
        st.markdown('<p class="main-header">Gestión de Aprovisionamiento (OC)</p>', unsafe_allow_html=True)
        
        tab_oc, tab_list, tab_guia_rec, tab_guia = st.tabs(["📝 Nueva Orden de Compra", "📜 Listado de OCs", "📦 Recepción (Guías)", "📖 Guía"])
        
        with tab_guia:
            render_aprovisionamiento_guide()
        
        
        with tab_oc:
            st.subheader("Crear Orden de Compra")
            
            # Cabecera OC
            c1, c2, c3, c4 = st.columns(4)
            df_prov = db.obtener_proveedores()
            opc_prov = df_prov['razon_social'].tolist() if not df_prov.empty else []
            
            prov_oc = c1.selectbox("Proveedor", ["Seleccionar..."] + opc_prov, key="o_prov")
            fecha_oc = c2.date_input("Fecha Emisión", date.today(), key="o_fecha")
            fecha_entrega = c3.date_input("Fecha Entrega Est.", date.today() + timedelta(days=7), key="o_fecha_ent")
            moneda_oc = c1.selectbox("Moneda", ["PEN", "USD"], key="o_moneda")
            
            tasa_igv = c4.number_input("Tasa IGV %", value=18.0, step=1.0, key="o_igv")
            obs_oc = st.text_area("Observaciones OC", key="o_obs")
            
            st.divider()
            st.markdown("##### Detalle de Items")
            
            df_prods = db.obtener_productos_extendido()
            if not df_prods.empty:
                df_prods['label'] = df_prods.apply(lambda x: f"{x['codigo_sku']} | {x['nombre']}", axis=1)
                df_prods['precio_ref_compra'] = df_prods['ultimo_precio_compra'].fillna(0.0)
                prod_map = df_prods.set_index('label')[['id', 'unidad_medida', 'precio_ref_compra']].to_dict('index')
                opc_prods = df_prods['label'].tolist()
            else:
                opc_prods = []
                prod_map = {}

            # Estado del Grid OC
            if 'df_oc_det' not in st.session_state:
                st.session_state.df_oc_det = pd.DataFrame(columns=[
                    "Producto", "U.M.", "Cantidad", "Precio Unit. (Inc. IGV)", "Valor Venta (Neto)", "IGV", "Total"
                ])

            col_conf_oc = {
                "Producto": st.column_config.SelectboxColumn("Producto", options=opc_prods, width="medium", required=True),
                "U.M.": st.column_config.TextColumn("U.M.", width="small", disabled=True),
                "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.01, step=0.01, width="small"),
                "Precio Unit. (Inc. IGV)": st.column_config.NumberColumn("Precio Unit. (Inc. IGV)", min_value=0.01, step=0.01, format="%.2f", width="medium"),
                "Valor Venta (Neto)": st.column_config.NumberColumn("Valor Neto", disabled=True, format="%.2f", width="medium"),
                "IGV": st.column_config.NumberColumn("IGV", disabled=True, format="%.2f", width="small"),
                "Total": st.column_config.NumberColumn("Total Línea", disabled=True, format="%.2f", width="medium"),
            }
            
            if 'key_oc' not in st.session_state:
                st.session_state.key_oc = 0

            # Sanitize columns
            valid_cols = ["Producto", "U.M.", "Cantidad", "Precio Unit. (Inc. IGV)", "Valor Venta (Neto)", "IGV", "Total"]
            
            # Strict cleanup
            if list(st.session_state.df_oc_det.columns) != valid_cols:
                clean_data = {col: st.session_state.df_oc_det[col] for col in valid_cols if col in st.session_state.df_oc_det}
                st.session_state.df_oc_det = pd.DataFrame(clean_data, columns=valid_cols)
            
            # Force reset index
            st.session_state.df_oc_det.reset_index(drop=True, inplace=True)

            edited_oc = st.data_editor(
                st.session_state.df_oc_det, 
                column_config=col_conf_oc, 
                num_rows="dynamic", 
                use_container_width=True, 
                hide_index=True,
                key=f"editor_oc_{st.session_state.key_oc}"
            )
            
            # Logic similar to app.py but cleaner if possible.
            # Reuse logic for simplicity
            if not edited_oc.equals(st.session_state.df_oc_det):
                 need_rerun = False
                 for i, row in edited_oc.iterrows():
                     if row["Producto"]:
                         prod_data = prod_map.get(row["Producto"])
                         if prod_data:
                             # 1. Auto-llenar U.M. (Robust)
                             current_um = str(row.get("U.M.", "")).strip()
                             target_um = str(prod_data.get('unidad_medida', 'UND')).strip()
                             if not target_um or target_um == 'nan': target_um = 'UND'
                             
                             if current_um != target_um:
                                 edited_oc.at[i, "U.M."] = target_um
                                 need_rerun = True
                             
                             # 2. Sugerir Precio (Last Purchase Price)
                             if pd.isna(row["Precio Unit. (Inc. IGV)"]) or row["Precio Unit. (Inc. IGV)"] == 0:
                                 price_sug = prod_data.get('precio_ref_compra', 0.0)
                                 if price_sug and price_sug > 0:
                                     edited_oc.at[i, "Precio Unit. (Inc. IGV)"] = float(price_sug)
                                     need_rerun = True
                                 
                         # 3. Calcular Desglose
                         qty = float(row["Cantidad"]) if not pd.isna(row["Cantidad"]) else 0
                         p_unit_inc_igv = float(row["Precio Unit. (Inc. IGV)"]) if not pd.isna(row["Precio Unit. (Inc. IGV)"]) else 0
                         
                         p_unit_neto = p_unit_inc_igv / (1 + tasa_igv/100)
                         subtotal_neto = qty * p_unit_neto
                         total_linea = qty * p_unit_inc_igv
                         igv_linea = total_linea - subtotal_neto
                         
                         cur_val = float(edited_oc.at[i, "Valor Venta (Neto)"]) if pd.notna(edited_oc.at[i, "Valor Venta (Neto)"]) else 0.0
                         cur_igv = float(edited_oc.at[i, "IGV"]) if pd.notna(edited_oc.at[i, "IGV"]) else 0.0
                         cur_tot = float(edited_oc.at[i, "Total"]) if pd.notna(edited_oc.at[i, "Total"]) else 0.0

                         if (abs(cur_val - subtotal_neto) > 0.01 or
                             abs(cur_igv - igv_linea) > 0.01 or
                             abs(cur_tot - total_linea) > 0.01):
                             
                             edited_oc.at[i, "Valor Venta (Neto)"] = subtotal_neto
                             edited_oc.at[i, "IGV"] = igv_linea
                             edited_oc.at[i, "Total"] = total_linea
                             need_rerun = True
                 
                 if need_rerun:
                     st.session_state.df_oc_det = edited_oc
                     st.session_state.key_oc += 1
                     st.rerun()

            # Footer
            total_oc_neto = st.session_state.df_oc_det["Valor Venta (Neto)"].sum()
            total_oc_igv = st.session_state.df_oc_det["IGV"].sum()
            total_oc_final = st.session_state.df_oc_det["Total"].sum()
            
            c_t1, c_t2, c_t3 = st.columns([6, 2, 2])
            c_t2.markdown(f"**Subtotal:** S/ {total_oc_neto:,.2f}")
            c_t2.markdown(f"**IGV ({tasa_igv}%):** S/ {total_oc_igv:,.2f}")
            c_t3.metric("Total OC", f"S/ {total_oc_final:,.2f}")

            if st.button("💾 GENERAR ORDEN DE COMPRA", type="primary"):
                if prov_oc == "Seleccionar...":
                     st.error("Selecciona proveedor.")
                elif edited_oc.empty:
                     st.error("Detalle vacío.")
                else:
                     # Obtener Proveedor ID
                     cursor = db.get_connection().cursor()
                     cursor.execute("SELECT id FROM proveedores WHERE razon_social = ?", (prov_oc,))
                     res_prov = cursor.fetchone()
                     
                     if res_prov:
                         pid_prov = res_prov[0]
                         items = []
                         try:
                             for i, row in edited_oc.iterrows():
                                 if row["Producto"] and row["Cantidad"] > 0:
                                     # Resolve PID from Map
                                     item_data = {
                                         "Producto": row["Producto"],
                                         "Cantidad": row["Cantidad"],
                                         "PrecioUnitario": row["Precio Unit. (Inc. IGV)"]
                                     }
                                     
                                     if row["Producto"] in prod_map:
                                         item_data["pid"] = prod_map[row["Producto"]]['id']
                                     
                                     items.append(item_data)
                             
                             res = db.registrar_orden_compra(pid_prov, fecha_oc, moneda_oc, items)
                             
                             if res['success']:
                                 st.success(f"✅ Orden de Compra #{res['orden_id']} generada exitosamente.")
                                 st.balloons()
                                 # Reset
                                 st.session_state.df_oc_det = pd.DataFrame(columns=[
                                    "Producto", "U.M.", "Cantidad", "Precio Unit. (Inc. IGV)", "Valor Venta (Neto)", "IGV", "Total"
                                 ])
                                 st.session_state.key_oc += 1
                                 st.rerun()
                             else:
                                 st.error(f"Error backend: {res['error']}")
                                 
                         except Exception as e:
                             st.error(f"Error procesando: {str(e)}")
                     else:
                         st.error("Proveedor no encontrado en BD.")
                     
                     if res['success']:
                         st.success(f"✅ Orden #{res['orden_id']} creada exitosamente")
                         st.balloons()
                         
                         # Limpiar campos del formulario
                         for key in list(st.session_state.keys()):
                             if key.startswith('o_'):
                                 del st.session_state[key]
                         
                         # Limpiar detalle
                         st.session_state.df_oc_det = pd.DataFrame(columns=["Producto", "U.M.", "Cantidad", "Precio Unit. (Inc. IGV)", "Valor Venta (Neto)", "IGV", "Total"])
                         
                         # Resetear key del editor para forzar recreación
                         st.session_state.key_oc = 0
                         
                         st.rerun()
                     else:
                         st.error(res.get('error', 'Error desconocido'))
                         
        with tab_list:
            st.subheader("Gestión de Ordenes de Compra")
            df_ocs = db.obtener_ordenes_compra()
            
            if not df_ocs.empty:
                # Basic Status Color Map
                def color_estado(val):
                    color = 'gray'
                    if val == 'APROBADA': color = 'green'
                    elif val == 'PENDIENTE': color = 'orange'
                    elif val == 'RECHAZADA': color = 'red'
                    elif val == 'FACTURADA': color = 'blue'
                    return f'color: {color}; font-weight: bold'

                st.dataframe(
                    df_ocs.style.applymap(color_estado, subset=['Estado']), 
                    use_container_width=True, 
                    hide_index=True
                )
                
                st.divider()
                st.markdown("##### Acciones")
                
                cA, cB = st.columns([1, 2])
                oc_id_sel = cA.selectbox("Seleccionar N° Orden", df_ocs['id'].tolist())
                
                # Get current status
                curr_status = df_ocs.loc[df_ocs['id'] == oc_id_sel, 'Estado'].values[0]
                cB.info(f"Estado Actual: **{curr_status}**")
                
                col_act1, col_act2, col_act3, col_act4 = st.columns(4)
                
                if col_act1.button("✅ Aprobar"):
                    db.actualizar_estado_oc(oc_id_sel, "APROBADA")
                    st.rerun()
                    
                if col_act2.button("🚫 Rechazar"):
                    db.actualizar_estado_oc(oc_id_sel, "RECHAZADA")
                    st.rerun()
                    
                if col_act3.button("🗑️ Anular"):
                    db.actualizar_estado_oc(oc_id_sel, "ANULADA")
                    st.rerun()

                # Conversion Logic
                if curr_status == "APROBADA":
                    if col_act4.button("📄 Convertir a Factura"):
                        st.session_state['convert_oc_id'] = oc_id_sel
                        st.rerun()
                
                # Conversion Form (Modal-like)
                if 'convert_oc_id' in st.session_state and st.session_state['convert_oc_id'] == oc_id_sel:
                    st.markdown("---")
                    st.markdown(f"#### 🧾 Convirtiendo OC #{oc_id_sel} a Factura")
                    
                    with st.form("form_convert_oc"):
                        c_inv1, c_inv2 = st.columns(2)
                        inv_serie = c_inv1.text_input("Serie Factura", value="F001")
                        inv_num = c_inv2.text_input("Número Factura")
                        inv_fecha = st.date_input("Fecha Emisión Factura", date.today())
                        
                        if st.form_submit_button("Confirmar Conversión"):
                            if inv_serie and inv_num:
                                ok, msg = db.convertir_oc_a_compra(oc_id_sel, inv_serie, inv_num, inv_fecha)
                                if ok:
                                    st.success(msg)
                                    del st.session_state['convert_oc_id']
                                    st.rerun()
                                else:
                                    st.error(msg)
                            else:
                                st.error("Serie y Número son obligatorios.")

            else:
                st.info("No hay órdenes registradas.")

        with tab_guia_rec:
            st.info("🔜 Módulo de Recepción (Guías) en construcción...")

