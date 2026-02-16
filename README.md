# ERP Servidor Local (v2.1)

Sistema de Gestión Empresarial (ERP) moderno y ligero, diseñado para funcionar en un servidor local. Combina un backend robusto en Python (FastAPI) con un frontend dinámico en React.

## 🚀 Características Principales

*   **Gestión de Inventario:** Control de stock, kardex valorizado, múltiples almacenes.
*   **Compras:** Registro de facturas, órdenes de compra y gestión de proveedores.
*   **Guías de Remisión:** Recepción de mercancía con trazabilidad total (OC -> Guía -> Factura).
*   **Dashboard:** KPIs en tiempo real, gráficos de evolución de gastos y stock crítico.
*   **Autenticación:** Sistema de usuarios con roles (Admin/User).
*   **Base de Datos:** SQLite optimizado para despliegue local sencillo.
*   **Diseño Moderno:** Interfaz limpia y responsiva con Tailwind CSS.

---

## ⚙️ Instalación y Ejecución Rápida

Para desplegar el proyecto en Windows:

1.  **Ejecutar el Launcher:** Haz doble clic en `start_app.bat`. 
    Este script se encargará de:
    - Crear el entorno virtual (`venv`) si no existe.
    - Instalar todas las librerías de Python necesarias automáticamente.
    - Iniciar el servidor Backend (Puerto 8000).
    - Instalar las dependencias de Node.js si faltan.
    - Iniciar la aplicación Frontend (Puerto 5173).

---

## 💾 Configuración de la Base de Datos

Si necesitas inicializar o resetear los datos:

### Opción A: Base de Datos Vacía
```bash
backend\venv\Scripts\python backend/scripts/init_db_schema.py backend/data/gestion_basica.db
```

### Opción B: Datos de Prueba (Recomendado)
```bash
backend\venv\Scripts\python backend/scripts/seed_data_v2.py
```
*   **Usuario:** `admin`
*   **Contraseña:** `admin`

---

## 💡 Sugerencias de Mejora
Consulta la carpeta `sugerencias_mejora/` para ver el plan detallado de optimización de arquitectura identificado durante el diagnóstico del sistema.

---
**Versión Actual:** 2.1 (Restauración de flujo original start_app.bat).
