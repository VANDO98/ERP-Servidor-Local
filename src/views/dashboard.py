import streamlit as st
import altair as alt
import pandas as pd
import src.backend as db
from src.theme_manager import get_chart_text_color

class DashboardView:
    def render(self, start_date, end_date):
        st.markdown(f'<p class="main-header"> 📊 Dashboard General ({start_date.strftime("%d/%m/%Y")} - {end_date.strftime("%d/%m/%Y")})</p>', unsafe_allow_html=True)
        
        # KPI Cards
        kpis = db.obtener_kpis_dashboard(start_date, end_date)
        tc_hoy = db.obtener_tipo_cambio_actual()
        
        # Use columns for layout
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("💰 Compras Totales", f"S/ {kpis['compras_monto']:,.2f}")
        k2.metric("📦 Salidas Totales", f"S/ {kpis['salidas_monto']:,.2f}")
        k3.metric("🏠 Valor. Act. (FIFO)", f"S/ {kpis['valor_inventario']:,.2f}")
        k4.metric("📝 Facturas", kpis['compras_docs'])
        k5.metric("💵 T.C. Referencial", f"S/ {tc_hoy:.3f}")
        
        st.divider()
        
        # 🚨 ALERTAS CRÍTICAS (Nuevo)
        st.subheader("🚨 Alertas Críticas")
        alertas = db.obtener_alertas_criticas()
        
        a1, a2, a3, a4 = st.columns(4)
        
        with a1:
            st.metric("🔴 Sin Stock", alertas['sin_stock']['count'], delta=None, delta_color="inverse")
            if alertas['sin_stock']['count'] > 0:
                with st.expander("Ver Productos"):
                    for item in alertas['sin_stock']['items'][:10]:
                        st.write(f"- {item}")
                    if len(alertas['sin_stock']['items']) > 10:
                        st.caption(f"... y {len(alertas['sin_stock']['items']) - 10} más")

        with a2:
            st.metric("⚠️ Sin Movimiento (>90d)", alertas['sin_movimiento']['count'], delta=None, delta_color="inverse")
            if alertas['sin_movimiento']['count'] > 0:
                with st.expander("Ver Productos"):
                    for item in alertas['sin_movimiento']['items'][:10]:
                        st.write(f"- {item}")
                    if len(alertas['sin_movimiento']['items']) > 10:
                        st.caption(f"... y {len(alertas['sin_movimiento']['items']) - 10} más")

        with a3:
            st.metric("💰 Compras Grandes (7d)", alertas['compras_grandes']['count'])
            if alertas['compras_grandes']['count'] > 0:
                with st.expander("Ver Documentos"):
                    for item in alertas['compras_grandes']['items'][:10]:
                        st.write(f"- {item}")
                    if len(alertas['compras_grandes']['items']) > 10:
                        st.caption(f"... y {len(alertas['compras_grandes']['items']) - 10} más")

        with a4:
            st.metric("⚡ Posibles Duplicados", alertas['facturas_duplicadas']['count'], delta=None, delta_color="inverse")
            if alertas['facturas_duplicadas']['count'] > 0:
                with st.expander("Ver Detalles"):
                    for item in alertas['facturas_duplicadas']['items'][:10]:
                        st.write(f"- {item}")
                    if len(alertas['facturas_duplicadas']['items']) > 10:
                        st.caption(f"... y {len(alertas['facturas_duplicadas']['items']) - 10} más")
        
        st.divider()
        
        # CHARTS
        chart_text_color = get_chart_text_color()
        
        # Fila 1: Stock Crítico + Rotación de Inventario (Nuevo)
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("🚦 Stock Crítico (Top 15)")
            df_stock = db.obtener_stock_critico()
            if not df_stock.empty:
                # Crear tabla con colores corregidos
                for _, row in df_stock.iterrows():
                    # "Sin Stock" y "Crítico" van en ROJO
                    if row['Estado'] in ['Sin Stock', 'Crítico']:
                        color = "🔴"
                    elif row['Estado'] == 'Bajo':
                        color = "🟡"
                    else:
                        color = "✅"
                    
                    st.markdown(f"{color} **{row['Producto']}**: {row['Stock']:.2f} {row['UM']} ({row['Estado']})")
            else:
                st.success("✅ No hay productos en stock crítico")
                
        with c2:
            st.subheader("🔄 Rotación de Inventario")
            df_rotacion = db.obtener_rotacion_inventario()
            if not df_rotacion.empty:
                chart_rotacion = alt.Chart(df_rotacion).mark_bar().encode(
                    x=alt.X('TotalSalidas:Q', title="Salidas (30d)", axis=alt.Axis(labelColor=chart_text_color, titleColor=chart_text_color)),
                    y=alt.Y('Producto:N', sort='-x', axis=alt.Axis(labelColor=chart_text_color, titleColor=chart_text_color)),
                    color=alt.Color('Tipo:N', scale=alt.Scale(domain=['Alta Rotación', 'Baja Rotación'], range=['#28a745', '#dc3545']), legend=alt.Legend(labelColor=chart_text_color, titleColor=chart_text_color)),
                    tooltip=['Producto', 'TotalSalidas', 'StockActual', 'UM']
                ).properties(height=350, background='transparent')
                st.altair_chart(chart_rotacion, use_container_width=True)
            else:
                st.info("Sin datos de salidas en los últimos 30 días")
        
        st.divider()
        
        # Fila 2: Top Proveedores + Gasto por Categoría (Existentes)
        c3, c4 = st.columns(2)
        
        with c3:
            st.subheader("🏆 Top Proveedores")
            df_top = db.obtener_top_proveedores(start_date, end_date)
            if not df_top.empty:
                df_top['MontoFmt'] = df_top['Monto'].apply(lambda x: f"S/ {x:,.2f}")
                
                # =============================================================================
                # GRÁFICO: TOP PROVEEDORES (EVOLUCIÓN DEL DISEÑO)
                # -----------------------------------------------------------------------------
                # Iteración 1: Circular (Donut) - Se descartó por solapamiento de etiquetas de nombres largos.
                # Iteración 2: Barras Horizontales - Muy legible, pero el usuario prefirió algo más visual.
                # Iteración 3: Treemap (Experimental) - Se intentó pero Altair 5.x requiere layouts manuales complejos.
                # Iteración 4 (ACTUAL): Waffle Chart (Grilla 10x10)
                #   - Razón: Representa proporcionalidad (%) de forma técnica y moderna sin solapar texto.
                #   - Mejoras: 
                #     1. Leyenda interactiva (bind='legend') que resalta la grilla.
                #     2. Paleta Seaborn 'Deep' para acabado profesional.
                #     3. Espaciado H/V balanceado con strokeWidth=1 y size=500.
                # =============================================================================
                # Custom Waffle Chart Logic (10x10 grid)
                def get_waffle(df, grid_size=10):
                    df = df.sort_values('Monto', ascending=False)
                    v_total = df['Monto'].sum()
                    
                    # Calcular cuántos cuadros tiene cada uno (total 100)
                    df['Squares'] = (df['Monto'] / v_total * 100).round().astype(int)
                    df['Porcentaje'] = (df['Monto'] / v_total * 100).apply(lambda x: f"{x:.1f}%")
                    
                    # Ajustar si la suma no es exactamente 100 por redondeo
                    diff = 100 - df['Squares'].sum()
                    if diff != 0 and not df.empty:
                        df.iloc[0, df.columns.get_loc('Squares')] += diff
                    
                    # Combinar nombre y % para la leyenda
                    df['ProveedorPct'] = df['Proveedor'] + " (" + df['Porcentaje'] + ")"
                    
                    # Generar grilla
                    data = []
                    current_idx = 0
                    current_sq_count = 0
                    
                    for y in range(grid_size):
                        for x in range(grid_size):
                            if current_idx < len(df):
                                data.append({
                                    'x': x,
                                    'y': y,
                                    'Proveedor': df.iloc[current_idx]['Proveedor'],
                                    'MontoFmt': df.iloc[current_idx]['MontoFmt'],
                                    'ProveedorPct': df.iloc[current_idx]['ProveedorPct'],
                                    'Porcentaje': df.iloc[current_idx]['Porcentaje']
                                })
                                current_sq_count += 1
                                if current_sq_count >= df.iloc[current_idx]['Squares']:
                                    current_idx += 1
                                    current_sq_count = 0
                    
                    return pd.DataFrame(data)

                df_waffle = get_waffle(df_top)
                
                # Selección interactiva vinculada a la LEYENDA y al GRÁFICO
                selection_waffle = alt.selection_point(fields=['ProveedorPct'], bind='legend', on='mouseover')

                # Chart: Waffle (Abalance de espaciado H/V)
                waffle_chart = alt.Chart(df_waffle).mark_square(
                    size=500, 
                    stroke='white',
                    strokeWidth=1
                ).encode(
                    x=alt.X('x:O', axis=None),
                    y=alt.Y('y:O', axis=None, sort='descending'),
                    color=alt.Color('ProveedorPct:N', 
                        scale=alt.Scale(range=["#4c72b0", "#dd8452", "#55a868", "#c44e52", "#8172b3", "#937860", "#da8bc3", "#8c8c8c", "#ccb974", "#64b5cd"]), 
                        legend=alt.Legend(
                            orient='bottom', 
                            title="Top Proveedores (% participación)",
                            labelFontSize=9,
                            titleFontSize=10,
                            labelColor=chart_text_color,
                            titleColor=chart_text_color,
                            columns=2,
                            labelLimit=0,
                            symbolType='square'
                        )
                    ),
                    tooltip=['Proveedor:N', 'MontoFmt:N', 'Porcentaje:N'],
                    opacity=alt.condition(selection_waffle, alt.value(1), alt.value(0.3))
                ).add_params(selection_waffle).properties(
                    height=360,
                    width=270,
                    background='transparent'
                )
                
                # Centrar usando columnas de Streamlit
                cw1, cw2, cw3 = st.columns([1, 6, 1])
                with cw2:
                    st.altair_chart(waffle_chart, use_container_width=False)
            else:
                st.info("Sin datos en este periodo.")
                
        with c4:
            st.subheader("🍩 Gasto por Categoría")
            df_cat = db.obtener_gastos_por_categoria(start_date, end_date)
            if not df_cat.empty:
                # Calcular porcentajes para las etiquetas
                total_cat = df_cat['Monto'].sum()
                df_cat['PorcNum'] = (df_cat['Monto'] / total_cat * 100)
                df_cat['Porcentaje'] = df_cat['PorcNum'].apply(lambda x: f"{x:.1f}%")
                df_cat['MontoFmt'] = df_cat['Monto'].apply(lambda x: f"S/ {x:,.2f}")
                # Combinar nombre y % para la leyenda
                df_cat['CategoriaPct'] = df_cat['Categoria'] + " (" + df_cat['Porcentaje'] + ")"
                
                # Selección interactiva vinculada a la LEYENDA y al GRÁFICO
                selection = alt.selection_point(fields=['CategoriaPct'], bind='legend', on='mouseover')
                
                # =============================================================================
                # GRÁFICO: GASTO POR CATEGORÍA (EVOLUCIÓN DEL DISEÑO)
                # -----------------------------------------------------------------------------
                # Iteración 1: Barras Verticales - Estándar, pero ocupaba mucho espacio horizontal.
                # Iteración 2 (ACTUAL): Donut Chart (Dona)
                #   - Razón: Mejor aprovechamiento del espacio en columnas de Streamlit.
                #   - Mejoras: 
                #     1. Leyenda al pie (orient='bottom') organizada en 3 columnas para evitar recortes.
                #     2. Porcentajes integrados directamente en la LEYENDA para lectura rápida.
                #     3. Etiquetas en el gráfico inteligentes (solo si >5%) para evitar amontonamiento.
                #     4. Interactividad completa (resaltado desde leyenda + tooltip detallado).
                # =============================================================================
                # Chart: Donut para Gasto por Categoría
                chart_cat = alt.Chart(df_cat).mark_arc(innerRadius=60, outerRadius=100).encode(
                    theta=alt.Theta("Monto:Q", stack=True),
                    color=alt.Color("CategoriaPct:N", 
                        scale=alt.Scale(range=["#4c72b0", "#55a868", "#c44e52", "#8172b3", "#937860", "#da8bc3", "#8c8c8c", "#ccb974", "#64b5cd", "#dd8452"]),
                        legend=alt.Legend(
                            title="Categorías (% participación)", 
                            labelColor=chart_text_color, 
                            titleColor=chart_text_color, 
                            orient='bottom',
                            labelFontSize=9,
                            titleFontSize=10,
                            columns=3,
                            labelLimit=0,
                            symbolType='circle'
                        )
                    ),
                    tooltip=['Categoria', 'MontoFmt', 'Porcentaje'],
                    opacity=alt.condition(selection, alt.value(1), alt.value(0.3))
                ).add_params(selection)
    
                # Etiquetas de porcentaje (Solo si > 5% para evitar amontonamiento)
                text_cat = chart_cat.mark_text(radius=135, fontWeight='bold', fontSize=10).encode(
                    text=alt.condition(alt.datum.PorcNum > 5, alt.Text("Porcentaje:N"), alt.value("")),
                    color=alt.value(chart_text_color),
                    opacity=alt.value(1)
                )

                # Centrar gráfico
                st.altair_chart((chart_cat + text_cat).properties(height=380, background='transparent'), use_container_width=True)
            else:
                st.info("Sin datos en este periodo.")
                
        # EVOLUCIÓN (Existente)
        st.divider()
        st.subheader("📈 Evolución de Compras (Soles)")
        df_evol = db.obtener_evolucion_compras(start_date, end_date)
        
        if not df_evol.empty:
            df_evol['Fecha'] = pd.to_datetime(df_evol['Fecha'])
            
            chart_evol = alt.Chart(df_evol).mark_bar().encode(
                x=alt.X('Fecha:T', axis=alt.Axis(format='%d %b', title="Fecha", labelColor=chart_text_color, titleColor=chart_text_color)),
                y=alt.Y('Monto:Q', axis=alt.Axis(format=',.2f', title="Monto (S/)", labelColor=chart_text_color, titleColor=chart_text_color)),
                tooltip=[alt.Tooltip('Fecha:T', format='%d %b %Y'), alt.Tooltip('Monto:Q', format=',.2f', title="Monto S/")]
            ).properties(height=300, background='transparent').interactive()
            
            st.altair_chart(chart_evol, use_container_width=True)
        else:
            st.info("No hay historial suficiente para graficar.")
