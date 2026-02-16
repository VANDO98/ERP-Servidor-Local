@echo off
setlocal
echo ===================================================
echo   LIMPIEZA PROFUNDA DEL ENTORNO - ERP Lite
echo ===================================================
echo.

echo 1. Eliminando artefactos de Python...
:: Eliminar __pycache__ recursivamente
for /d /r . %%d in (__pycache__) do @if exist "%%d" (
    echo   - Eliminando %%d
    rd /s /q "%%d"
)
:: Eliminar archivos .pyc y .pyo
del /s /q *.pyc *.pyo >nul 2>&1

echo 2. Eliminando entornos virtuales antiguos...
if exist "venv" (
    echo   - Eliminando raiz/venv...
    rd /s /q "venv"
)
if exist "backend\venv" (
    echo   - Eliminando backend/venv...
    rd /s /q "backend\venv"
)

echo 3. Limpiando Frontend (Node.js/Vite)...
if exist "frontend\node_modules" (
    echo   - Eliminando frontend/node_modules...
    rd /s /q "frontend\node_modules"
)
if exist "frontend\dist" (
    echo   - Eliminando frontend/dist...
    rd /s /q "frontend\dist"
)
if exist "frontend\.vite" (
    echo   - Eliminando cache de Vite (.vite)...
    rd /s /q "frontend\.vite"
)

echo 4. Verificando archivos legacy...
if exist "backend\tienda.db" (
    echo   - [AVISO] Se detecto 'tienda.db'. No se borra por seguridad (esquema antiguo).
)

echo.
echo ===================================================
echo   LIMPIEZA COMPLETA FINALIZADA
echo ===================================================
echo Proximos pasos:
echo 1. Ejecuta 'instalar_dependencias_backend.bat'
echo 2. Ejecuta 'npm install' dentro de la carpeta frontend (si borraste node_modules)
echo 3. Inicia el sistema con 'iniciar_erp.bat'
echo.
pause
endlocal
