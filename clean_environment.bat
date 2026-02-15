@echo off
echo ===================================================
echo   LIMPIEZA PROFUNDA DEL ENTORNO
echo ===================================================
echo.

echo 1. Eliminando carpetas __pycache__...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo 2. Eliminando entornos virtuales antiguos...
if exist "venv" (
    echo   - Eliminando raiz/venv...
    rd /s /q "venv"
)
if exist "backend\venv" (
    echo   - Eliminando backend/venv...
    rd /s /q "backend\venv"
)

echo 3. Limpiando archivos temporales...
if exist "backend\tienda.db" (
    echo   - (Opcional) backend/tienda.db encontrado (Legacy). No se borra por seguridad.
)

echo.
echo ===================================================
echo   LIMPIEZA COMPLETA
echo ===================================================
echo Ahora ejecuta start_app.bat para reinstalar todo.
echo.
pause
