# Tareas Pendientes (Archivado)

Estas tareas han sido pospuestas para priorizar la implementación del sistema de Autenticación y Seguridad.

## 1. Corrección de Impresión PDF
- **Ubicación**: `frontend/src/pages/Orders.jsx`
- **Problema**: Error reportado al intentar generar/imprimir el PDF de una Orden de Compra.
- **Acción**: Depurar la función `handlePrint`, verificar datos pasados al componente de impresión.

## 2. Revisión Lógica Kardex
- **Ubicación**: `backend/src/backend.py` (`obtener_kardex_valorizado`)
- **Problema**: Verificar que el cálculo de saldos y costos promedios sea consistente con la nueva lógica FIFO por almacén.
- **Acción**: Auditar y testear la función con casos borde.

## 3. Formato de Plantillas de Datos
- **Ubicación**: `backend/main.py` (`get_template`)
- **Problema**: Las plantillas CSV actuales pueden no abrirse correctamente en Excel debido a separadores o codificación.
- **Acción**: Cambiar separador a punto y coma (`;`) o usar formato Excel nativo (`.xlsx`) y asegurar BOM para UTF-8.
