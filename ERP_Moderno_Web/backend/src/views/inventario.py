import streamlit as st
import pandas as pd
import src.backend as db

class InventarioView:
    def render(self):
        st.markdown('<p class="main-header">Gestión de Inventarios y Kardex</p>', unsafe_allow_html=True)
        
        tab_valorizado, tab_kardex = st.tabs(["💰 Resumen Valorizado (FIFO)", "📜 Kardex por Producto"])
        
        with tab_valorizado:
            # Controls
            c_ctrl1, c_ctrl2 = st.columns([1, 2])
            vista_inv = c_ctrl1.radio("Visualización", ["Global (FIFO)", "Por Almacén (Detallado)"], horizontal=True)
            incluir_igv = c_ctrl2.checkbox("Incluir IGV en Valorización", value=True, help="Si marcas esto, el valor incluirá impuestos.")

            if vista_inv == "Global (FIFO)":
                # Obtener valores FIFO detallados (Pasamos el flag)
                total_val_fifo, map_fifo = db.calcular_valorizado_fifo(incluir_igv=incluir_igv)
                df_inv = db.obtener_productos_extendido()
                
                if not df_inv.empty:
                    # Asignar valor FIFO row por row
                    df_inv['valor_fifo'] = df_inv['id'].map(lambda x: map_fifo.get(x, {}).get('valor', 0.0))
                    # Costo Promedio Referencial
                    df_inv['costo_unit_ref'] = df_inv.apply(lambda x: x['valor_fifo'] / x['stock_actual'] if x['stock_actual'] > 0 else 0, axis=1)

                    label_costo = "Costo Promedio (Ref)"
                    label_total = "Total Valorizado (FIFO)"

                    st.info("ℹ️ **Global FIFO:** El sistema asume que el stock sale en el orden que entró, independientemente del almacén.")

                    st.dataframe(
                        df_inv[['codigo_sku', 'nombre', 'categoria_nombre', 'unidad_medida', 'stock_actual', 'costo_unit_ref', 'valor_fifo']].rename(
                            columns={
                                'stock_actual': 'Stock Global',
                                'costo_unit_ref': label_costo,
                                'valor_fifo': label_total
                            }
                        ).style.format({
                            "Stock Global": "{:.2f}",
                            label_costo: "S/ {:,.2f}",
                            label_total: "S/ {:,.2f}"
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    st.metric(f"💰 Valor Total ({'INC. IGV' if incluir_igv else 'NETO'})", f"S/ {total_val_fifo:,.2f}")
                else:
                    st.info("Inventario vacío.")
            
            else: # Por Almacén
                st.info("ℹ️ **Detalle por Almacén:** Muestra la ubicación física del stock. La valorización aquí es referencial (Costo Promedio).")
                df_det = db.obtener_inventario_detallado()
                
                if not df_det.empty:
                    # Calculate value based on Avg Cost (Ref)
                    # Note: incluir_igv logic affects Avg Cost if we want strict consistency, 
                    # but CostoPromedio in DB usually is NET (if logic is sound). 
                    # Assuming CostoPromedio in DB is NET. If user wants IGV, we multiply by 1.18
                    
                    factor = 1.18 if incluir_igv else 1.0
                    df_det['CostoUnitRef'] = df_det['CostoUnitRef'] * factor
                    df_det['ValorTotal'] = df_det['Stock'] * df_det['CostoUnitRef']
                    
                    st.dataframe(
                        df_det.style.format({
                            "Stock": "{:.2f}",
                            "CostoUnitRef": "S/ {:,.2f}",
                            "ValorTotal": "S/ {:,.2f}"
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    total_val = df_det['ValorTotal'].sum()
                    st.metric(f"💰 Valor Total Referencial", f"S/ {total_val:,.2f}")
                else:
                    st.warning("No hay stock en almacenes.")

        with tab_kardex:
            st.subheader("Consulta de Movimientos por Producto")
            
            # Buscador de producto
            df_items = db.obtener_productos_extendido()
            if not df_items.empty:
                df_items['label'] = df_items.apply(lambda x: f"{x['codigo_sku']} | {x['nombre']}", axis=1)
                map_items = dict(zip(df_items['label'], df_items['id']))
                
                selected_label = st.selectbox("Seleccione un producto para ver su historial", ["Seleccionar..."] + list(map_items.keys()))
                
                if selected_label != "Seleccionar...":
                    pid = map_items[selected_label]
                    df_kardex = db.obtener_kardex_producto(pid)
                    
                    if not df_kardex.empty:
                        st.markdown(f"**Historial para:** {selected_label}")
                        
                        # Formatear tabla
                        st.dataframe(
                            df_kardex.style.format({
                                "Entrada": "{:.2f}",
                                "Salida": "{:.2f}",
                                "Saldo": "{:.2f}"
                            }),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Resumen rápido
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Entradas Totales", f"{df_kardex['Entrada'].sum():,.2f}")
                        c2.metric("Salidas Totales", f"{df_kardex['Salida'].sum():,.2f}")
                        c3.metric("Stock Actual Calculado", f"{df_kardex['Saldo'].iloc[-1]:,.2f}")
                    else:
                        st.info("No se registran movimientos para este producto.")
            else:
                st.warning("No hay productos registrados para consultar el Kardex.")

