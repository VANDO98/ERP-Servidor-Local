@echo off
setlocal
echo ====================================================
echo   Instalador de Dependencias del Backend - ERP Lite
echo ====================================================
cd backend

:: Verificar integridad del entorno virtual
if exist "venv" (
    if not exist "venv\Scripts\activate.bat" (
        echo [!] El entorno virtual esta incompleto o corrupto. Recreando...
        rd /s /q venv
    )
)

if not exist "venv" (
    echo [INFO] Creando entorno virtual nuevo...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] No se pudo crear el entorno virtual. 
        echo Asegurate de tener Python instalado y accesible desde la consola.
        pause
        exit /b
    )
)

echo [INFO] Instalando/Actualizando librerias...
call venv\Scripts\activate
if errorlevel 1 (
    echo [ERROR] No se pudo activar el entorno virtual.
    pause
    exit /b
)

python -m pip install --upgrade pip
pip install -r requirements.txt

echo ====================================================
echo   Instalacion completada satisfactoriamente.
echo ====================================================
pause
endlocal
