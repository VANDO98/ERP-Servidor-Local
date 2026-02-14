@echo off
echo ===================================================
echo   INICIANDO ERP WEB MODERNO (v2.0)
echo ===================================================
echo.

REM 1. Iniciar Backend (FastAPI) usando el VENV
echo Lanzando Backend...
start "ERP Backend API" /min cmd /k "cd /d %~dp0backend && title ERP Backend && call ..\venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"
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
npm run dev

pause
