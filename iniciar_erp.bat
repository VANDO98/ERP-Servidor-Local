@echo off
setlocal
echo ====================================================
echo   Iniciando Servidores ERP Lite - Validador v3
echo ====================================================

:: 1. Validar Backend e Integridad del VENV
echo [1/2] Verificando Backend...
if not exist "backend\venv\Scripts\activate.bat" (
    echo [ERROR] El entorno virtual 'backend\venv' no existe o esta incompleto.
    echo [!] Por favor, ejecuta primero 'instalar_dependencias_backend.bat' para repararlo.
    pause
    exit /b
)

:: 2. Validar Frontend y node_modules
echo [2/2] Verificando Frontend...
if not exist "frontend\node_modules" (
    echo [INFO] No se encontro 'frontend\node_modules'. Instalando dependencias...
    echo Esto puede tardar un momento...
    cd frontend && call npm install && cd ..
)

echo.
echo ====================================================
echo   Lanzando aplicaciones...
echo ====================================================

:: Lanzar Backend en una nueva ventana
start "Backend - FastAPI" cmd /k "cd backend && call venv\Scripts\activate && python main.py"

:: Lanzar Frontend en una nueva ventana
start "Frontend - Vite" cmd /k "cd frontend && npm run dev"

echo.
echo Servidores en proceso de arranque.
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:5173
echo.
echo No cierres las ventanas que se acaban de abrir.
pause
endlocal
