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

## ⚙️ Instalación desde Cero

Sigue estos pasos para desplegar el proyecto en un nuevo entorno:

### 1. Clonar el Repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd "ERP servidor local"
```

### 2. Configuración del Backend
```bash
cd backend
python -m venv venv
# Activar entorno virtual
# En Windows:
..\venv\Scripts\activate
# En Linux/Mac: source ../venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
cd ..
```

### 3. Configuración del Frontend
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
*   **Limpieza de Entorno:** Ejecuta `clean_environment.bat` si encuentras conflictos con librerías o carpetas `venv` duplicadas.
*   **Dependencias:** El sistema verifica automáticamente las librerías al inicio (`check_dependencies.py`), pero puedes instalarlas manualmente con `pip install -r backend/requirements.txt`.

## 🔄 Control de Versiones (Git)
El proyecto incluye un `.gitignore` optimizado para evitar subir archivos temporales (`__pycache__`, `venv`, `.db`).

---
**Versión Actual:** 2.1 (Incluye corrección de estado de OCs y mejoras en validación de dependencias).
Desarrollado para gestión eficiente en entornos locales.
