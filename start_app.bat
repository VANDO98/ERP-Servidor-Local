@echo off
setlocal

echo ===================================================
echo   INICIANDO ERP WEB MODERNO (v2.2)
echo ===================================================
echo.

REM 1. Verificar VENV
if not exist "backend\venv\Scripts\python.exe" (
    echo [ERROR] No se detecto el entorno virtual.
    echo Por favor ejecuta primero: setup_env.bat
    pause
    exit /b
)

REM 2. Verificar Node.js
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js no esta disponible en esta sesion.
    echo Si lo acabas de instalar, por favor REINICIA TU TERMINAL.
    pause
    exit /b
)

REM 3. Verificar node_modules
if not exist "frontend\node_modules" (
    echo [ERROR] Faltan dependencias del Frontend.
    echo Por favor ejecuta primero: setup_env.bat
    pause
    exit /b
)

echo [INFO] Lanzando Backend...
start "ERP-Backend" /min cmd /k "cd /d %~dp0backend && call venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo [INFO] Lanzando Frontend...
cd frontend
start "ERP-Frontend" /min cmd /k "npm run dev -- --host"
cd ..

echo [INFO] Abriendo navegador...
timeout /t 5 /nobreak >nul
start http://localhost:5173/login

echo.
echo ===================================================
echo   SISTEMA INICIADO
echo ===================================================
pause
exit /b
