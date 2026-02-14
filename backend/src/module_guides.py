"""
Módulo de Guías de Usuario para cada sección del sistema.
Proporciona información sobre cómo usar cada módulo y sus beneficios.
"""

import streamlit as st

def render_dashboard_guide():
    """Guía del módulo Dashboard"""
    st.markdown("""
    ## 📊 Guía del Dashboard
    
    ### ¿Qué es?
    El Dashboard es tu centro de control visual que te permite monitorear el estado general de tu negocio en tiempo real.
    
    ### ¿Qué puedes hacer aquí?
    
    #### 1. **KPIs Principales**
    - 💰 **Compras Totales**: Monto total gastado en el periodo seleccionado
    - 📦 **Valor de Inventario**: Valor actual de tu stock calculado con método FIFO
    - 📝 **Facturas**: Número de documentos de compra registrados
    - 💵 **Tipo de Cambio**: Referencia actual para conversiones USD/PEN
    
    #### 2. **Alertas Críticas** 🚨
    - 🔴 **Sin Stock**: Productos agotados que necesitan reabastecimiento urgente
    - ⚠️ **Sin Movimiento**: Productos con stock pero sin salidas en más de 90 días (posible obsolescencia)
    - 💰 **Compras Grandes**: Compras superiores a S/ 10,000 en los últimos 7 días (control de gastos)
    - ⚡ **Posibles Duplicados**: Facturas con mismo proveedor, fecha y monto (prevención de errores)
    
    #### 3. **Stock Crítico** 🚦
    Muestra los 10 productos con stock más bajo comparado con su consumo promedio:
    - 🔴 **Crítico**: Stock ≤ 20% del consumo mensual promedio
    - 🟡 **Bajo**: Stock ≤ 50% del consumo mensual promedio
    
    #### 4. **Rotación de Inventario** 🔄
    Identifica productos de alta y baja rotación en los últimos 30 días:
    - **Alta Rotación** (verde): Productos más vendidos/usados
    - **Baja Rotación** (rojo): Productos con poco movimiento
    
    #### 5. **Top Proveedores** 🏆
    Gráfico circular que muestra la distribución de gastos por proveedor.
    
    #### 6. **Gasto por Categoría** 🍩
    Barras horizontales mostrando en qué categorías de productos gastas más.
    
    #### 7. **Evolución de Compras** 📈
    Gráfico de barras temporal mostrando la tendencia de compras día a día.
    
    ### Beneficios
    - ✅ **Visión 360°** de tu negocio en un solo lugar
    - ✅ **Detección temprana** de problemas (stock crítico, duplicados)
    - ✅ **Optimización de inventario** (identificar productos lentos)
    - ✅ **Control de gastos** por proveedor y categoría
    - ✅ **Toma de decisiones** basada en datos reales
    
    ### Consejos
    💡 Ajusta el rango de fechas en la barra lateral para analizar periodos específicos.
    
    💡 Revisa las alertas críticas diariamente para acción inmediata.
    
    💡 Usa la rotación de inventario para negociar mejores precios en productos de alta demanda.
    """)

def render_aprovisionamiento_guide():
    """Guía del módulo Aprovisionamiento"""
    st.markdown("""
    ## 📝 Guía de Aprovisionamiento (Órdenes de Compra)
    
    ### ¿Qué es?
    El módulo de Aprovisionamiento te permite crear y gestionar Órdenes de Compra (OC) formales antes de realizar la compra.
    
    ### ¿Qué puedes hacer aquí?
    
    #### 1. **Crear Orden de Compra**
    - Selecciona proveedor, fecha de emisión y entrega estimada
    - Agrega productos con cantidades y precios
    - El sistema auto-completa la U.M. y precio de referencia
    - Calcula automáticamente subtotales, IGV y total
    
    #### 2. **Listado de OCs**
    - Visualiza todas las órdenes generadas
    - Filtra por estado, proveedor o fecha
    
    ### Beneficios
    - ✅ **Planificación**: Organiza tus compras antes de ejecutarlas
    - ✅ **Control presupuestario**: Aprueba gastos antes de comprometer dinero
    - ✅ **Trazabilidad**: Historial completo de órdenes emitidas
    - ✅ **Negociación**: Documento formal para enviar a proveedores
    
    ### Flujo Recomendado
    1. Revisa el Dashboard para identificar productos en stock crítico
    2. Crea una OC con esos productos
    3. Envía la OC al proveedor
    4. Al recibir la factura, regístrala en el módulo "Compras"
    
    ### Consejos
    💡 Usa las OCs para consolidar compras y negociar mejores precios por volumen.
    
    💡 La fecha de entrega estimada te ayuda a planificar el flujo de caja.
    """)

def render_compras_guide():
    """Guía del módulo Compras"""
    st.markdown("""
    ## 🛒 Guía de Compras (Facturas)
    
    ### ¿Qué es?
    El módulo de Compras registra las facturas reales de proveedores y actualiza automáticamente tu inventario y costos.
    
    ### ¿Qué puedes hacer aquí?
    
    #### 1. **Registrar Compra**
    - Ingresa datos de la factura (proveedor, serie, número, fecha)
    - Selecciona moneda (PEN/USD) y tipo de cambio
    - Agrega productos con cantidades y precios unitarios
    - **Conversión de Unidades**: Puedes comprar en ML y se convertirá automáticamente a LITRO
    - El sistema calcula IGV y totales automáticamente
    
    #### 2. **Historial Resumen**
    - Lista de todas las facturas registradas
    - Totales por factura
    
    #### 3. **Historial Detallado**
    - Desglose línea por línea de cada factura
    - Útil para auditorías y análisis de precios
    
    ### Beneficios
    - ✅ **Actualización automática** de stock y costos
    - ✅ **Método FIFO**: Valorización precisa del inventario
    - ✅ **Control de duplicados**: Alertas de facturas similares
    - ✅ **Multi-moneda**: Soporte para USD y PEN
    - ✅ **Conversión de unidades**: Flexibilidad en compras (ML, GR, CM, etc.)
    - ✅ **Auditoría completa**: Historial detallado de todas las compras
    
    ### Conversión de Unidades 🔄
    El sistema soporta conversión automática entre unidades de la misma familia:
    - **Volumen**: LITRO ↔ ML ↔ GLN ↔ M3
    - **Masa**: KG ↔ GR ↔ TON ↔ LB
    - **Longitud**: METRO ↔ CM ↔ MM
    
    **Ejemplo**: Si tu producto base es LITRO pero compras 500 ML, el sistema:
    1. Guarda en la factura "500 ML" (auditoría)
    2. Actualiza el stock en "0.5 LITRO" (inventario)
    
    ### Consejos
    💡 Verifica siempre la serie y número de factura para evitar duplicados.
    
    💡 Si compras en USD, asegúrate de ingresar el tipo de cambio correcto del día.
    
    💡 Usa el historial detallado para comparar precios entre proveedores.
    """)

def render_salidas_guide():
    """Guía del módulo Salidas"""
    st.markdown("""
    ## 📤 Guía de Salidas / Servicios
    
    ### ¿Qué es?
    El módulo de Salidas registra el consumo o venta de productos, reduciendo el stock automáticamente.
    
    ### ¿Qué puedes hacer aquí?
    
    #### 1. **Registrar Salida**
    - Selecciona tipo de salida (Venta, Consumo Interno, Servicio, Merma, etc.)
    - Ingresa fecha y observaciones
    - Agrega productos con cantidades
    - El sistema descuenta automáticamente del stock
    
    #### 2. **Historial de Salidas**
    - Lista completa de todas las salidas registradas
    - Filtros por tipo, fecha o producto
    
    ### Beneficios
    - ✅ **Control de stock**: Mantén tu inventario actualizado
    - ✅ **Trazabilidad**: Saber qué se usó, cuándo y para qué
    - ✅ **Análisis de consumo**: Identifica patrones de uso
    - ✅ **Cálculo de rotación**: Base para las métricas del Dashboard
    - ✅ **Prevención de faltantes**: Detecta consumo excesivo
    
    ### Tipos de Salida
    - **Venta**: Producto vendido a clientes
    - **Consumo Interno**: Uso en operaciones propias
    - **Servicio**: Producto usado en prestación de servicios
    - **Merma**: Pérdida por deterioro, vencimiento, etc.
    - **Ajuste**: Correcciones de inventario
    
    ### Consejos
    💡 Registra las salidas diariamente para mantener el stock preciso.
    
    💡 Usa el campo "Observaciones" para detallar el destino o motivo.
    
    💡 Las mermas te ayudan a identificar productos problemáticos.
    """)

def render_inventario_guide():
    """Guía del módulo Inventario"""
    st.markdown("""
    ## 📦 Guía de Inventario (Kardex Valorizado)
    
    ### ¿Qué es?
    El módulo de Inventario muestra el Kardex Valorizado, un reporte contable que detalla todos los movimientos de cada producto.
    
    ### ¿Qué puedes hacer aquí?
    
    #### 1. **Kardex Valorizado**
    - Selecciona un producto
    - Elige el método de valorización (FIFO o Promedio Ponderado)
    - Define el rango de fechas
    - Visualiza movimiento por movimiento:
      - Fecha y tipo de operación
      - Entradas (compras)
      - Salidas (consumos/ventas)
      - Saldo físico y valorizado
      - Costo unitario
    
    ### Métodos de Valorización
    
    #### **FIFO (First In, First Out)**
    - "Lo primero que entra, es lo primero que sale"
    - Más preciso para productos perecederos
    - Refleja mejor el costo real de reposición
    - **Recomendado para**: Alimentos, medicinas, productos con vencimiento
    
    #### **Promedio Ponderado**
    - Calcula un costo promedio de todas las compras
    - Más simple y estable
    - Suaviza fluctuaciones de precios
    - **Recomendado para**: Materiales de construcción, repuestos, productos no perecederos
    
    ### Beneficios
    - ✅ **Cumplimiento contable**: Reporte oficial para auditorías
    - ✅ **Control de costos**: Conoce el costo real de tu inventario
    - ✅ **Detección de errores**: Identifica movimientos anómalos
    - ✅ **Toma de decisiones**: Base para fijar precios de venta
    - ✅ **Análisis de márgenes**: Compara costo vs precio de venta
    
    ### Consejos
    💡 Usa FIFO si tus productos tienen fecha de vencimiento.
    
    💡 Revisa el Kardex mensualmente para detectar inconsistencias.
    
    💡 El saldo valorizado debe coincidir con tu contabilidad.
    """)

def render_maestros_guide():
    """Guía del módulo Gestión de Datos"""
    st.markdown("""
    ## ⚙️ Guía de Gestión de Datos (Maestros)
    
    ### ¿Qué es?
    El módulo de Gestión de Datos es donde creas y mantienes la información base del sistema: productos, proveedores y categorías.
    
    ### ¿Qué puedes hacer aquí?
    
    #### 1. **Proveedores** 👥
    - Crear, editar y eliminar proveedores
    - Registrar: RUC, razón social, contacto, teléfono, email, categoría
    - **Carga Masiva**: Importa múltiples proveedores desde Excel
    - Descarga plantilla Excel para facilitar la carga
    
    #### 2. **Productos** 📦
    - Crear, editar y eliminar productos
    - Registrar: SKU, nombre, categoría, unidad de medida, stock inicial
    - **Carga Masiva**: Importa múltiples productos desde Excel
    - Descarga plantilla Excel para facilitar la carga
    
    #### 3. **Categorías** 🏷️
    - Crear categorías para organizar productos
    - Ejemplos: Alimentos, Limpieza, Oficina, Construcción, etc.
    - Útil para análisis de gastos por categoría
    
    #### 4. **Carga Masiva** 📤
    - Descarga plantillas Excel pre-formateadas
    - Llena los datos en Excel
    - Sube el archivo y el sistema valida e importa automáticamente
    - Ahorra tiempo al registrar muchos elementos
    
    ### Beneficios
    - ✅ **Base de datos organizada**: Información centralizada y estructurada
    - ✅ **Ahorro de tiempo**: Carga masiva para registros múltiples
    - ✅ **Validación automática**: El sistema detecta errores en los datos
    - ✅ **Categorización**: Facilita análisis y reportes
    - ✅ **Actualización fácil**: Edita información en cualquier momento
    
    ### Buenas Prácticas
    
    #### Para Productos:
    - Usa códigos SKU únicos y descriptivos
    - Asigna la categoría correcta para análisis precisos
    - Define la unidad de medida base (LITRO, KG, UND, etc.)
    - Ingresa stock inicial si ya tienes inventario
    
    #### Para Proveedores:
    - Verifica el RUC en SUNAT antes de registrar
    - Completa email y teléfono para comunicación
    - Usa categorías para agrupar (Ej: "Alimentos", "Servicios")
    
    #### Para Carga Masiva:
    - Descarga siempre la plantilla actualizada
    - No modifiques los encabezados de las columnas
    - Revisa que no haya filas vacías entre datos
    - Guarda como .xlsx (no .xls ni .csv)
    
    ### Consejos
    💡 Empieza creando las categorías antes de los productos.
    
    💡 Usa la carga masiva si tienes más de 10 productos/proveedores.
    
    💡 Mantén actualizada la información de contacto de proveedores.
    
    💡 Revisa periódicamente productos duplicados o en desuso.
    """)
