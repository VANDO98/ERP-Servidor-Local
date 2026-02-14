# Prueba de Estilos de Tablas

import streamlit as st
import pandas as pd
from src.theme_manager import get_theme_css, get_chart_text_color

st.set_page_config(page_title="Test Tablas", layout="wide")

# Theme state
if 'theme_dark' not in st.session_state:
    st.session_state.theme_dark = False

# Inject CSS
st.markdown(get_theme_css(st.session_state.theme_dark), unsafe_allow_html=True)

# Theme toggle
with st.sidebar:
    st.markdown("### 🎨 Tema")
    new_theme = st.toggle("🌙 Modo Oscuro", value=st.session_state.theme_dark)
    if new_theme != st.session_state.theme_dark:
        st.session_state.theme_dark = new_theme
        st.rerun()

st.title("🧪 Test de Estilos - Tablas y Selectbox")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 DataFrame (Solo lectura)")
    df = pd.DataFrame({
        'Producto': ['Laptop', 'Mouse', 'Teclado', 'Monitor'],
        'Precio': [1500.00, 25.50, 120.00, 450.00],
        'Stock': [10, 50, 30, 15]
    })
    st.dataframe(df, use_container_width=True)
    
    st.markdown(f"**Tema actual:** {'🌙 Oscuro' if st.session_state.theme_dark else '☀️ Claro'}")
    st.markdown("**¿Ves el texto en negro sobre fondo blanco?**")

with col2:
    st.subheader("✏️ DataEditor (Editable)")
    df_edit = st.data_editor(df, use_container_width=True, num_rows="dynamic")
    
    st.markdown("**¿Puedes editar y ver el texto?**")
    
    st.subheader("📋 Selectbox Test")
    selected = st.selectbox("Selecciona un producto", df['Producto'].tolist())
    st.write(f"Seleccionaste: **{selected}**")
    st.markdown("**¿Se ve la línea transparente en modo oscuro?**")

# Debug info
st.divider()
st.subheader("🔍 Debug Info")
st.code(f"""
Tema actual: {st.session_state.theme_dark}
Color de texto para gráficos: {get_chart_text_color(st.session_state.theme_dark)}

CSS aplicado: {'Dark Mode' if st.session_state.theme_dark else 'Light Mode'}
""")

st.markdown("""
### ✅ Checklist de Verificación

**Modo Claro (☀️):**
- [ ] DataFrame: Fondo blanco, texto negro visible
- [ ] DataEditor: Fondo blanco, texto negro visible
- [ ] Selectbox: Fondo blanco, texto negro visible
- [ ] Selectbox dropdown: Fondo blanco, opciones en negro

**Modo Oscuro (🌙):**
- [ ] DataFrame: Fondo oscuro, texto blanco visible
- [ ] DataEditor: Fondo oscuro, texto blanco visible
- [ ] Selectbox: Fondo oscuro, texto blanco visible, **SIN línea transparente**
- [ ] Selectbox dropdown: Fondo oscuro, opciones en blanco
""")
