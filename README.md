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

## 🛠️ Tecnologías

*   **Backend:** Python 3.10+, FastAPI, SQLite, Pandas.
*   **Frontend:** React 18, Vite, Tailwind CSS, Lucide Icons.
*   **Herramientas:** Git, NPM.

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:
*   [Python 3.10+](https://www.python.org/downloads/) (Asegúrate de marcar "Add Python to PATH" durante la instalación).
*   [Node.js 18+](https://nodejs.org/es/) (Incluye NPM).
*   [Git](https://git-scm.com/).

---

## ⚙️ Instalación Automática (Recomendado)

El proyecto incluye scripts automatizados para Windows que facilitan la configuración.

### 1. Clonar el Repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd "ERP servidor local"
```

### 2. Configuración Inicial (`setup_env.bat`)
Ejecuta el archivo `setup_env.bat` (doble clic o desde terminal).
Este script se encargará de:
1.  Crear el entorno virtual (`venv`) para el backend.
2.  Instalar todas las dependencias de Python (`requirements.txt`).
3.  Inicializar la Base de Datos SQLite.
4.  (Opcional) Cargar datos de prueba iniciales (Semilla).

### 3. Instalación Frontend
Si es la primera vez, instala las dependencias de node:
```bash
cd frontend
npm install
cd ..
```

---

## 💾 Configuración de la Base de Datos

El sistema utiliza SQLite. Puedes iniciar con una base de datos vacía o con datos de prueba.

### Opción A: Base de Datos Vacía (Estructura Limpia)
Utiliza el script de inicialización para crear las tablas necesarias:
```bash
# Estando en la raíz del proyecto
backend\venv\Scripts\python backend/scripts/init_db_schema.py backend/data/gestion_basica.db
```

### Opción B: Datos de Semilla (Usuario Admin)
Para crear el usuario administrador por defecto y datos básicos:
```bash
backend\venv\Scripts\python backend/scripts/seed_data_v2.py
```
*   **Usuario:** `admin`
*   **Contraseña:** `admin`

---

## ▶️ Ejecución del Sistema

### Modo Automático (Recomendado)
Simplemente ejecuta el archivo `start_app.bat` (doble clic) en Windows.
Este script se encargará de:
1.  Verificar e instalar librerías de Python faltantes.
2.  Iniciar el servidor Backend (Puerto 8000).
3.  Instalar dependencias de Frontend si faltan.
4.  Iniciar la aplicación web (Puerto 5173).

### Modo Manual
**Terminal 1 (Backend):**
```bash
cd backend
..\venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

---

## 📂 Estructura del Proyecto

```
ERP servidor local/
├── backend/
│   ├── data/           # Base de datos (gestion_basica.db)
│   ├── scripts/        # Scripts de mantenimiento (init_db, seed, backup)
│   ├── src/            # Lógica de negocio y endpoints
│   └── main.py         # Punto de entrada de la API
├── frontend/
│   ├── src/            # Componentes React y páginas
│   └── public/         # Assets estáticos
├── start_app.bat       # Launcher automático para Windows
└── README.md           # Esta documentación
```

## 📦 Migración y Mantenimiento

### Scripts de Base de Datos
*   **Inicialización:** `backend/scripts/init_db_schema.py`
    *   Genera una base de datos vacía con la estructura más reciente.
    *   Uso: `python backend/scripts/init_db_schema.py <ruta_nueva_db>`
*   **Exportación:** `backend/scripts/export_schema.py`
    *   Extrae el esquema actual de la base de datos en producción para actualizar el script de inicialización.
*   **Semilla:** `backend/scripts/seed_data_v2.py`
    *   Puebla la base de datos con datos de prueba y usuario admin.

### Solución de Problemas
*   **Limpieza de Entorno:** Ejecuta `clean_env.bat`. Este script elimina el entorno virtual (`venv`) y los archivos caché (`__pycache__`), permitiendo una instalación limpia desde cero con `setup_env.bat`.
*   **Dependencias:** El sistema verifica automáticamente las librerías al inicio (`check_dependencies.py`).

## 🔐 Seguridad y Sesión
*   **Token de Sesión:** Duración extendida de **12 horas** para evitar desconexiones durante la jornada laboral.
*   **Control de Inactividad:** El sistema detecta inactividad tras **10 minutos**. Mostrará una alerta 60 segundos antes de cerrar sesión automáticamente para validar tu presencia.

## 🔄 Control de Versiones (Git)
El proyecto incluye un `.gitignore` optimizado para evitar subir archivos temporales (`__pycache__`, `venv`, `.db`).

---
**Versión Actual:** 2.2 (Refactorización Modular, Scripts de Gestión y Control de Sesión).
Desarrollado para gestión eficiente en entornos locales.
