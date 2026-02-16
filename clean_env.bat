@echo off
setlocal

echo ===================================================
echo   LIMPIEZA DE ENTORNO DE DESARROLLO (clean_env.bat)
echo ===================================================
echo.
echo [ADVERTENCIA] Esto eliminara:
echo  - Carpeta backend\venv (Entorno Virtual)
echo  - Archivos __pycache__
echo  - Archivos .pytest_cache
echo.
set /p CONFIRM="¿Estas seguro de continuar? (S/N): "
if /i not "%CONFIRM%"=="S" goto end

echo.
REM 1. Eliminar VENV
if exist "backend\venv" (
    echo [INFO] Eliminando entorno virtual...
    rmdir /s /q "backend\venv"
    echo [OK] Venv eliminado.
) else (
    echo [INFO] Venv no existe.
)

REM 2. Eliminar Cache (Recursivo en backend)
echo [INFO] Limpiando caches...
cd backend
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d"
cd ..
echo [OK] Caches limpiados.

echo.
echo [OK] Limpieza completada. Ejecuta setup_env.bat para reinstalar.

:end
pause
endlocal
