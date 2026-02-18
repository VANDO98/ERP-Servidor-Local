@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   CONFIGURACION DE ENTORNO ERP (v2.2)
echo ===================================================
echo.

REM 1. Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no encontrado en el PATH.
    echo Por favor instala Python 3.12+ y marca "Add Python to PATH".
    pause
    exit /b
)
echo [OK] Python detectado.

REM 2. Verificar Node.js
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Node.js no encontrado. Intentando instalar...
    winget install -e --id OpenJS.NodeJS --accept-source-agreements --accept-package-agreements
    echo [IMPORTANTE] Por favor, CIERRA Y REABRE esta ventana de comandos para que el sistema reconozca Node.js.
    pause
    exit /b
)
echo [OK] Node.js detectado.

REM 3. Gestionar Entorno Virtual
if not exist "backend\venv\Scripts\python.exe" goto :CREATE_VENV

echo [INFO] Entorno virtual ya existe.
set /p RECREATE="Desea RECREAR el entorno virtual? (S/N): "
if /i "!RECREATE!"=="S" (
    echo [INFO] Eliminando entorno antiguo...
    rd /s /q "backend\venv"
    goto :CREATE_VENV
)
goto :VENV_DONE

:CREATE_VENV
echo [INFO] Creando entorno virtual...
python -m venv backend\venv
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b
)
echo [OK] Entorno virtual creado.

:VENV_DONE

REM 4. Dependencias del Backend
echo [INFO] Instalando dependencias del Backend...
call backend\venv\Scripts\python.exe -m pip install --upgrade pip
call backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Error instalando dependencias de Python.
    pause
    exit /b
)
echo [OK] Dependencias del Backend listas.

REM 5. Dependencias del Frontend
echo [INFO] Instalando dependencias del Frontend (NPM)...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo [ERROR] Error instalando dependencias de Node.js.
    cd ..
    pause
    exit /b
)
cd ..
echo [OK] Dependencias del Frontend listas.

REM 6. Base de Datos
echo [INFO] Configurando Base de Datos...
if not exist "backend\data" mkdir "backend\data"

if not exist "backend\data\gestion_basica.db" goto :INIT_DB
set /p REINIT="La DB ya existe. Desea REINICIALIZARLA? (S/N): "
if /i "!REINIT!"=="S" (
    del "backend\data\gestion_basica.db"
    goto :INIT_DB
)
goto :DB_DONE

:INIT_DB
echo [INFO] Inicializando esquema...
call backend\venv\Scripts\python.exe backend\scripts\init_db_schema.py backend\data\gestion_basica.db
if %errorlevel% neq 0 (
    echo [ERROR] Error al inicializar la base de datos.
    pause
    exit /b
)
echo [OK] Base de datos inicializada.

:DB_DONE

echo.
echo ===================================================
echo   CONFIGURACION COMPLETADA EXITOSAMENTE
echo   Ahora puedes ejecutar start_app.bat
echo ===================================================
pause
exit /b
