import streamlit as st
import pandas as pd
from datetime import date
import src.backend as db
from src.unit_converter import get_compatible_units
from src.module_guides import render_compras_guide

class ComprasView:
    def render(self):
        st.markdown('<p class="main-header">Gestión de Compras</p>', unsafe_allow_html=True)
        
        tab_reg, tab_hist, tab_det, tab_guia = st.tabs(["📝 Registrar Compra", "📜 Historial (Resumen)", "🔍 Historial (Detallado)", "📖 Guía"])
        
        with tab_guia:
            render_compras_guide()
        
        
        with tab_reg:
            # 1. Cabecera
            df_prov = db.obtener_proveedores()
            mapa_proveedores = dict(zip(df_prov['razon_social'], df_prov['id'])) if not df_prov.empty else {}
            
            # Obtener Almacenes
            df_alm = db.obtener_almacenes()
            mapa_almacenes = dict(zip(df_alm['nombre'], df_alm['id'])) if not df_alm.empty else {1: "Principal"}
            
            c1, c2, c3 = st.columns([2, 1, 1])
            prov_name = c1.selectbox("Proveedor", ["Seleccionar..."] + list(mapa_proveedores.keys()), key="c_prov")
            alm_name = c2.selectbox("Almacén", list(mapa_almacenes.keys()), key="c_alm_sel")
            
            if c3.button("➕ Crear Prov."):
                st.info("Ve a la pestaña Maestros para crear nuevos.")

            d1, d2, d3, d4, d5 = st.columns([2, 1.5, 1.5, 1.5, 1.5])
            f_emision = d1.date_input("Fecha", date.today(), key="c_fecha")
            serie = d2.text_input("Serie", key="c_serie")
            numero = d3.text_input("Número", key="c_num")
            moneda = d4.selectbox("Moneda", ["PEN", "USD"], key="c_moneda")
            
            tc_def = db.obtener_tipo_cambio_actual()
            if moneda == "USD":
                tc = d4.text_input("Tipo Cambio", value=str(tc_def), key="c_tc")
            else:
                tc = "1.0"
                st.caption(f"T.C. Ref: S/ {tc_def}")
                
            tasa_igv_compra = d5.number_input("IGV %", value=18.0, step=1.0, key="c_igv")
            
            # Validación Duplicados (Backend helper?)
            # Assuming logic exists or we skip for now to keep it simple
            
            st.divider()
            st.markdown("##### 📦 Detalle de Ítems")
            
            # Cargar productos
            df_prods = db.obtener_productos_extendido()
            if not df_prods.empty:
                df_prods['label'] = df_prods.apply(lambda x: f"{x['codigo_sku'] or ''} | {x['nombre']}", axis=1)
                df_prods['precio_ref_compra'] = df_prods['ultimo_precio_compra'].fillna(0.0)
                prod_map = df_prods.set_index('label')[['id', 'unidad_medida', 'precio_ref_compra']].to_dict('index')
                opciones_prods = df_prods['label'].tolist()
            else:
                opciones_prods = []
                prod_map = {}

            if 'df_compras' not in st.session_state:
                st.session_state.df_compras = pd.DataFrame(columns=[
                    "Producto", "U.M.", "Cantidad", "Precio Unit. (Inc. IGV)", "Valor Venta (Neto)", "IGV", "Total"
                ])
                
            # Prepare ALL possible U.M. options (for initial display)
            # Note: We'll dynamically filter per row based on product's base unit
            standard_ums = ["UND", "KG", "GR", "TON", "LB", "LITRO", "ML", "GLN", "M3", "METRO", "CM", "MM", "CAJA", "LATE", "BOLSA"]
            existing_ums = [x for x in df_prods['unidad_medida'].unique().tolist() if pd.notna(x) and str(x).strip() != ""] if not df_prods.empty else []
            all_ums_options = sorted(list(set(standard_ums + existing_ums)))

            col_conf_compra = {
                "Producto": st.column_config.SelectboxColumn("Producto", options=opciones_prods, width="medium", required=True),
                "U.M.": st.column_config.TextColumn("U.M.", width="small", disabled=True),
                "Cantidad": st.column_config.NumberColumn("Cantidad", min_value=0.001, step=0.001, width="small"),
                "Precio Unit. (Inc. IGV)": st.column_config.NumberColumn("Precio Unit. (Inc. IGV)", min_value=0.01, step=0.01, format="%.2f", width="medium"),
                "Valor Venta (Neto)": st.column_config.NumberColumn("Valor Neto", disabled=True, format="%.2f", width="medium"),
                "IGV": st.column_config.NumberColumn("IGV", disabled=True, format="%.2f", width="small"),
                "Total": st.column_config.NumberColumn("Total", disabled=True, format="%.2f", width="medium"),
            }
            
            if 'key_compras' not in st.session_state:
                st.session_state.key_compras = 0

            # Sanitize columns to remove ghost # or index columns
            valid_cols = ["Producto", "U.M.", "Cantidad", "Precio Unit. (Inc. IGV)", "Valor Venta (Neto)", "IGV", "Total"]
            
            # Strict cleanup: Rebuild DF if columns don't match exactly
            if list(st.session_state.df_compras.columns) != valid_cols:
                clean_data = {col: st.session_state.df_compras[col] for col in valid_cols if col in st.session_state.df_compras}
                st.session_state.df_compras = pd.DataFrame(clean_data, columns=valid_cols)
            
            # Ensure proper types for auto-fill to work
            st.session_state.df_compras['U.M.'] = st.session_state.df_compras['U.M.'].astype(str).replace('nan', '')

            # Force reset index to ensure no index artifacts
            st.session_state.df_compras.reset_index(drop=True, inplace=True)

            edited_df = st.data_editor(
                st.session_state.df_compras, 
                column_config=col_conf_compra, 
                num_rows="dynamic", 
                use_container_width=True, 
                hide_index=True,
                key=f"editor_compras_{st.session_state.key_compras}"
            )
            
            # Mostrar ayuda sobre unidades compatibles
            if not st.session_state.df_compras.empty and st.session_state.df_compras['Producto'].notna().any():
                with st.expander("ℹ️ Guía de Unidades Compatibles"):
                    st.markdown("""
                    **Familias de Unidades:**
                    - **Volumen**: LITRO, ML, GLN, M3
                    - **Masa**: KG, GR, TON, LB
                    - **Longitud**: METRO, CM, MM
                    - **Unidad**: UND, CAJA, BOLSA, LATE (sin conversión)
                    
                    💡 **Tip**: Puedes comprar en cualquier unidad de la misma familia. Ej: Si el producto es LITRO, puedes comprar en ML y se convertirá automáticamente.
                    """)

            # Recálculo y validación
            if not edited_df.equals(st.session_state.df_compras):
                 need_rerun = False
                 validation_warnings = []
                 
                 for i, row in edited_df.iterrows():
                     if row["Producto"]:
                         prod_name = row["Producto"]
                         prod_data = prod_map.get(prod_name)
                         
                     if prod_data:
                             # 1. Auto-llenar U.M. (Simple & Robust)
                             current_um = str(row.get("U.M.", "")).strip()
                             target_um = str(prod_data.get('unidad_medida', 'UND')).strip()
                             if not target_um or target_um == 'nan': target_um = 'UND'
                             
                             # Force update if different to ensure consistency
                             if current_um != target_um:
                                 edited_df.at[i, "U.M."] = target_um
                                 need_rerun = True
                             
                             # 2. Auto-llenar Precio (Si es 0 o vacío)
                             current_price = row.get("Precio Unit. (Inc. IGV)", 0.0)
                             if pd.isna(current_price) or current_price == 0:
                                 last_price = prod_data.get('precio_ref_compra', 0.0) 
                                 if last_price and last_price > 0:
                                     edited_df.at[i, "Precio Unit. (Inc. IGV)"] = float(last_price)
                                     need_rerun = True

                     # Re-calculate line totals
                     qty = float(row["Cantidad"]) if not pd.isna(row["Cantidad"]) else 0
                     # Reload price in case it was updated above
                     p_inc_igv = float(edited_df.at[i, "Precio Unit. (Inc. IGV)"]) if not pd.isna(edited_df.at[i, "Precio Unit. (Inc. IGV)"]) else 0
                     
                     p_neto = p_inc_igv / (1 + tasa_igv_compra/100)
                     subtotal = qty * p_neto
                     total = qty * p_inc_igv
                     igv = total - subtotal
                     
                     cur_val = float(edited_df.at[i, "Valor Venta (Neto)"]) if pd.notna(edited_df.at[i, "Valor Venta (Neto)"]) else 0.0
                     cur_igv = float(edited_df.at[i, "IGV"]) if pd.notna(edited_df.at[i, "IGV"]) else 0.0
                     cur_tot = float(edited_df.at[i, "Total"]) if pd.notna(edited_df.at[i, "Total"]) else 0.0

                     if (abs(cur_val - subtotal) > 0.01 or abs(cur_igv - igv) > 0.01 or abs(cur_tot - total) > 0.01):
                         edited_df.at[i, "Valor Venta (Neto)"] = subtotal
                         edited_df.at[i, "IGV"] = igv
                         edited_df.at[i, "Total"] = total
                         need_rerun = True
                 
                 # Mostrar advertencias de validación
                 if validation_warnings:
                     for warning in validation_warnings:
                         st.warning(warning)
                 
                 if need_rerun:
                    st.session_state.df_compras = edited_df
                    st.session_state.key_compras += 1
                    st.rerun()

            # Footer
            total_neto = st.session_state.df_compras["Valor Venta (Neto)"].sum()
            total_igv = st.session_state.df_compras["IGV"].sum()
            total_final = st.session_state.df_compras["Total"].sum()
            sym = "$" if moneda == "USD" else "S/"
            
            c_t1, c_t2, c_t3 = st.columns([6, 2, 2])
            c_t2.markdown(f"**Subtotal:** {sym} {total_neto:,.2f}")
            c_t2.markdown(f"**IGV ({tasa_igv_compra}%):** {sym} {total_igv:,.2f}")
            c_t3.markdown(f"### Total a Pagar")
            c_t3.markdown(f"## {sym} {total_final:,.2f}")
            
            st.write("") 
            
            if st.button("💾 GUARDAR COMPRA", type="primary", use_container_width=True):
                 if prov_name == "Seleccionar..." or st.session_state.df_compras.empty:
                     st.error("Faltan datos.")
                 else:
                     detalles_list = []
                     for _, row in st.session_state.df_compras.iterrows():
                         if row["Producto"]:
                             detalles_list.append({
                                 "pid": prod_map[row["Producto"]]['id'], # Correct key: pid
                                 "descripcion": row["Producto"],
                                 "unidad_medida": row["U.M."],
                                 "cantidad": row["Cantidad"],
                                 "precio_unitario": row["Precio Unit. (Inc. IGV)"], 
                                 "subtotal": row["Valor Venta (Neto)"], # Backend might use this
                                 "tasa_impuesto": tasa_igv_compra
                             })
                     
                     prov_id = mapa_proveedores[prov_name]
                     tc_final = float(tc) if moneda == "USD" else 1.0
                     
                     cab = {
                        "proveedor_id": prov_id, "fecha": f_emision, # Backend expects 'fecha' in registrar_compra
                        "tipo_documento": "FACTURA", "serie": serie, "numero_documento": f"{serie}-{numero}", # Logic in backend uses numero_documento
                        "moneda": moneda, "tipo_cambio": tc_final,
                        "total": total_final, # Backend uses 'total' to split base/igv
                        'almacen_id': mapa_almacenes[alm_name]
                     }
                     
                     ok = False
                     msg = ""
                     try:
                         res = db.registrar_compra(cab, detalles_list)
                         if res['success']:
                             ok = True
                             msg = f"Compra registrada ID: {res['compra_id']}"
                         else:
                             ok = False
                             msg = res.get('error', 'Error')
                     except Exception as e:
                         ok = False
                         msg = str(e)
                         
                     if ok:
                          st.balloons()
                          st.success(msg)
                          
                          # Limpiar completamente el formulario
                          st.session_state.df_compras = pd.DataFrame(columns=["Producto", "U.M.", "Cantidad", "Precio Unit. (Inc. IGV)", "Valor Venta (Neto)", "IGV", "Total"])
                          
                          # Limpiar campos del formulario
                          for key in list(st.session_state.keys()):
                              if key.startswith('c_'):
                                  del st.session_state[key]
                          
                          # Resetear key del editor para forzar recreación
                          st.session_state.key_compras = 0
                          
                          st.rerun()
                     else:
                         st.error(msg)
                                
        with tab_hist:
            st.subheader("Historial (Resumen)")
            df_hist = db.obtener_historial_compras()
            if not df_hist.empty:
                st.dataframe(df_hist, use_container_width=True)
            else:
                st.info("No hay compras registradas aún.")
                
        with tab_det:
            st.subheader("Historial Detallado")
            df_det = db.obtener_historial_compras_detallado()
            
            if not df_det.empty:
                def highlight_change(row):
                    costo_ant = row['costo_previo'] if not pd.isna(row['costo_previo']) else 0
                    precio_new = row['precio_unitario']
                    if costo_ant == 0: return [""] * len(row)
                    if precio_new > costo_ant: return ['color: #EF4444; font-weight: bold' if col == 'precio_unitario' else '' for col in row.index]
                    elif precio_new < costo_ant: return ['color: #10B981; font-weight: bold' if col == 'precio_unitario' else '' for col in row.index]
                    return [""] * len(row)

                st.dataframe(
                    df_det.style.format({
                        "cantidad": "{:.2f}",
                        "costo_previo": "S/ {:.2f}",
                        "precio_unitario": "S/ {:.2f}",
                        "subtotal": "S/ {:.2f}"
                    }).apply(highlight_change, axis=1), 
                    use_container_width=True
                )
            else:
                st.info("No hay movimientos registrados.")
