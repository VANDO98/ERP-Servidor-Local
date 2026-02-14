@echo off
echo ===================================================
echo   INICIANDO ERP WEB MODERNO (v2.0)
echo ===================================================
echo.

REM 1. Iniciar Backend (FastAPI) usando el VENV
echo Lanzando Backend...
start "ERP Backend API" /min cmd /k "cd /d %~dp0 && title ERP Backend && venv\Scripts\python.exe -m uvicorn ERP_Moderno_Web.backend.main:app --reload --host 0.0.0.0 --port 8000"
echo [OK] Backend API iniciado en segundo plano.

REM 2. Iniciar Frontend (React/Vite)
echo Lanzando Frontend...
cd ERP_Moderno_Web\frontend
echo Instalando dependencias faltantes por si acaso...
call npm install
echo Iniciando servidor de desarrollo...
npm run dev

pause
