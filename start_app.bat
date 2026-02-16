@echo off
echo ===================================================
echo   INICIANDO ERP WEB MODERNO (v2.0)
echo ===================================================
echo.

REM 1. Validar Entorno Virtual (VENV)
if not exist "backend\venv" (
    echo [INFO] No se encontro entorno virtual. Creando venv...
    python -m venv backend\venv
    if %errorlevel% neq 0 (
        echo [ERROR] No se pudo crear el entorno virtual. Asegurate de tener Python instalado y en el PATH.
        pause
        exit /b
    )
    echo [OK] Entorno virtual creado.
    
    echo [INFO] Actualizando pip...
    call backend\venv\Scripts\python.exe -m pip install --upgrade pip
)

REM 2. Validar e Instalar Dependencias
echo Verificando librerias necesarias...
call backend\venv\Scripts\python.exe backend\check_dependencies.py
if %errorlevel% neq 0 (
    echo [ERROR] No se pudieron instalar las dependencias. Intente ejecutar manualmente: pip install -r backend/requirements.txt
    pause
    exit /b
)
echo.

REM 2. Iniciar Backend (FastAPI) usando el VENV
echo Lanzando Backend...
start "ERP Backend API" /min cmd /k "cd /d %~dp0backend && title ERP Backend && call venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo [OK] Backend API iniciado en segundo plano (puerto 8000).
echo.

REM 2. Esperar 3 segundos para que el backend se inicie
timeout /t 3 /nobreak >nul

REM 3. Iniciar Frontend (React/Vite)
echo Lanzando Frontend...
cd frontend
echo Instalando dependencias si es necesario...
call npm install --silent
echo Iniciando servidor de desarrollo...
npm run dev -- --host


REM 4. Abrir Navegador
echo Abriendo aplicacion en navegador...
start http://localhost:5173/login

pause
