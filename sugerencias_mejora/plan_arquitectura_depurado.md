# Plan de Optimización de Arquitectura y Estabilidad - ERP Lite

Este documento detalla las mejoras críticas necesarias para estabilizar el sistema y resolver fallos de visualización de datos (como los 0.00 en el Dashboard).

## 1. Problemas Identificados (Diagnóstico)

### 🔴 Redundancia de Código Crítica
- **`backend.py`**: Existen múltiples definiciones de funciones esenciales como `registrar_compra`, `obtener_compras_historial` y `obtener_ordenes_compra`. Algunas versiones usan parámetros distintos, lo que causa fallos aleatorios dependiendo de cuál se cargue en memoria.
- **`main.py`**: Los endpoints de FastAPI están duplicados. Por ejemplo, hay dos rutas para `/api/purchases/summary`. La primera define una lógica que falla, y la segunda (más abajo en el archivo) sobreescribe la anterior.

### 🔴 Discrepancia en Esquema de Datos
- Se han encontrado consultas SQL que intentan acceder a `purchase_id` cuando la columna real en la base de datos SQLite es `compra_id`. Esto genera excepciones que el backend captura silenciosamente, devolviendo listas vacías `[]` al frontend.

### 🔴 Lógica de KPIs Defectuosa
- La función `obtener_kpis_dashboard` utiliza `f-strings` para inyectar el tipo de cambio directamente en el SQL. Si la API de SUNAT devuelve un valor inesperado o `None`, la consulta colapsa.
- Comparación de fechas: Se mezclan objetos `datetime.date` con strings ISO en las consultas `BETWEEN`.

---

## 2. Plan de Acción Recomendado

### Fase A: Limpieza de Redundancias
1. **Consolidar `backend.py`**: Eliminar todas las definiciones duplicadas. Mantener solo una versión robusta de cada función que maneje correctamente las excepciones y los tipos de datos.
2. **Consolidar `main.py`**: Eliminar endpoints repetidos. Agrupar los endpoints por categorías (Auth, Maestros, Transacciones, Reportes).

### Fase B: Estandarización de Consultas
1. **Normalizar nombres de columnas**: Asegurar que todas las consultas SQL usen `compra_id`, `proveedor_id`, etc., según el esquema definido en `init_db_schema.py`.
2. **SQL Seguro**: Cambiar las `f-strings` por parámetros `?` en todas las consultas para evitar inyección SQL y errores de formato.

### Fase C: Mejoras Funcionales
1. **Manejo de T.C. (Tipo de Cambio)**: Implementar un fallback persistente en la tabla `tipo_cambio` para que el sistema nunca dependa 100% de la conectividad con la API de SUNAT en tiempo real.
2. **Validación de Fechas**: Asegurar que el frontend envíe siempre `YYYY-MM-DD` y el backend lo trate como string para las comparaciones de SQLite, que es lo más eficiente.

---

## 3. Aspectos a Revisar y Validar

### En el Backend:
- [ ] Ejecutar `python backend/main.py` y observar si hay advertencias de "Duplicate route" en la consola de FastAPI.
- [ ] Validar que `obtener_kpis_dashboard` no devuelva `0.00` cuando hay datos en `compras_cabecera`.
- [ ] Verificar que `registrar_compra` actualice tanto `stock_actual` en la tabla `productos` como en `stock_almacen`.

### En el Frontend:
- [ ] Comprobar que el componente `Dashboard.jsx` reciba correctamente el objeto `kpis` con las llaves `compras_monto`, `salidas_monto` y `valor_inventario`.
- [ ] Revisar la consola del navegador (F12) para detectar errores `404` o `500` en las llamadas a `/api/dashboard/complete`.

---

## 4. Próximos Pasos Sugeridos
Se recomienda realizar la limpieza de `main.py` primero, ya que es el punto de entrada. Una vez que los endpoints sean únicos y apunten a las funciones correctas en `backend.py`, los errores de "datos en cero" desaparecerán.
