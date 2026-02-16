@echo off
setlocal

echo ===================================================
echo   CONFIGURACION DE ENTORNO ERP (setup_env.bat)
echo ===================================================
echo.

REM 1. Crear entorno virtual si no existe
if not exist "backend\venv" (
    echo [INFO] Creando entorno virtual (python -m venv)...
    python -m venv backend\venv
    if %errorlevel% neq 0 (
        echo [ERROR] Fallo al crear venv. Verifica tu instalacion de Python.
        pause
        exit /b
    )
    echo [OK] Venv creado exitosamente.
) else (
    echo [INFO] Entorno virtual ya existe (backend\venv).
)

REM 2. Actualizar pip e instalar dependencias
echo [INFO] Instalando/Actualizando dependencias...
call backend\venv\Scripts\python.exe -m pip install --upgrade pip
call backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al instalar dependencias. Revisa internet o requirements.txt.
    pause
    exit /b
)
echo [OK] Dependencias lista.

REM 3. Inicializar Base de Datos
echo [INFO] Inicializando esquema de Base de Datos...
call backend\venv\Scripts\python.exe backend\scripts\init_db_schema.py
if %errorlevel% neq 0 (
    echo [ERROR] Fallo al inicializar DB.
    pause
    exit /b
)
echo [OK] Base de Datos inicializada (gestion_basica.db).

REM 4. Cargar Datos de Prueba (Opcional)
echo.
set /p DUMMY="¿Desea cargar DATOS DE EJEMPLO? (S/N): "
if /i "%DUMMY%"=="S" (
    echo [INFO] Cargando datos semilla...
    call backend\venv\Scripts\python.exe backend\scripts\seed_data_v2.py
    if %errorlevel% equ 0 (
        echo [OK] Datos cargados exitosamente.
    ) else (
        echo [ERROR] Hubo un problema cargando datos.
    )
)

echo.
echo ===================================================
echo   CONFIGURACION COMPLETADA
echo   Ahora puedes ejecutar start_app.bat
echo ===================================================
pause
endlocal
