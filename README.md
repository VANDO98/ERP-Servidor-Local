# ERP Servidor Local (v2.0)

Sistema de Gestión Empresarial (ERP) moderno y ligero, diseñado para funcionar en un servidor local. Combina un backend robusto en Python (FastAPI) con un frontend dinámico en React.

## 🚀 Características

*   **Gestión de Inventario:** Control de stock, kardex valorizado, múltiples almacenes.
*   **Compras:** Registro de facturas, órdenes de compra, gestión de proveedores.
*   **Dashboard:** KPIs en tiempo real, gráficos de evolución de gastos y stock crítico.
*   **Autenticación:** Sistema de usuarios con roles (Admin/User).
*   **Base de Datos:** SQLite optimizado para despliegue local sencillo.
*   **Diseño Moderno:** Interfaz limpia y responsiva con Tailwind CSS.

## 🛠️ Tecnologías

*   **Backend:** Python 3.10+, FastAPI, SQLite, Pandas.
*   **Frontend:** React 18, Vite, Tailwind CSS, Lucide Icons.
*   **Herramientas:** Git, NPM.

## 📋 Requisitos Previos

*   Python 3.10 o superior.
*   Node.js 18 o superior.
*   Git.

## ⚙️ Instalación y Ejecución

### Opción Rápida (Recomendada)

Simplemente ejecuta el script `start_app.bat` que se encuentra en la raíz del proyecto. Este script se encargará de:
1.  Iniciar el servidor backend en segundo plano.
2.  Instalar dependencias del frontend si faltan.
3.  Iniciar la aplicación web.

### Instalación Manual

1.  **Backend:**
    ```bash
    cd backend
    python -m venv venv
    ..\venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000
    ```

2.  **Frontend:**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## 📂 Estructura del Proyecto

```
ERP servidor local/
├── backend/            # API REST (FastAPI)
│   ├── data/           # Base de datos SQLite
│   ├── scripts/        # Scripts de utilidad (seed, backup)
│   ├── src/            # Lógica de negocio
│   └── main.py         # Punto de entrada de la API
├── frontend/           # Aplicación Web (React + Vite)
│   ├── src/            # Componentes y páginas
│   └── public/         # Assets estáticos
├── _BACKUP_LEGACY/     # Archivos de versiones anteriores
├── start_app.bat       # Script de inicio rápido
└── README.md           # Documentación
```

## 🔐 Credenciales por Defecto

Al inicializar la base de datos (usando `backend/scripts/seed_data_v2.py`), se crea un usuario administrador por defecto:

*   **Usuario:** `admin`
*   **Contraseña:** `admin`

## 📦 Copias de Seguridad

El sistema incluye scripts para realizar copias de seguridad automáticas de la base de datos en la carpeta `backend/backups`.

---
Desarrollado para gestión eficiente en entornos locales.
