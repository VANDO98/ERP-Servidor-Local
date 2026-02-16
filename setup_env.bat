@echo off
setlocal

echo ===================================================
echo   CONFIGURACION DE ENTORNO ERP (setup_env.bat)
echo ===================================================
echo.



REM 1. Verificar Instalacion de Python
echo [INFO] Verificando Python...
python --version >nul 2>&1
if %errorlevel% equ 0 goto :PYTHON_FOUND

:PYTHON_MISSING
echo [WARN] Python no encontrado. Intentando instalar via Winget...
winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
if %errorlevel% neq 0 (
    echo [ERROR] No se pudo instalar Python automaticamente.
    echo Por favor instala Python 3.12+ desde https://python.org
    pause
    exit /b
)
echo [OK] Python instalado correctamente.
echo Por favor CIERRA y REABRE esta ventana para aplicar los cambios en el PATH.
pause
exit /b

:PYTHON_FOUND
echo [INFO] Python detectado.
REM Intentamos actualizar silenciosamente, si falla no importa.
winget upgrade -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python actualizado.
) else (
    echo [INFO] Python ya esta actualizado o Winget no disponible. Continuamos...
)

:CREATE_VENV

REM 2. Crear entorno virtual
if not exist "backend\venv" (
    echo [INFO] Creando entorno virtual...
    python -m venv backend\venv
    if %errorlevel% neq 0 (
        echo [ERROR] Fallo al crear venv.
        pause
        exit /b
    )
    echo [OK] Venv creado exitosamente.
) else (
    echo [INFO] Entorno virtual ya existe.
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
echo [INFO] Verificando Base de Datos...
if not exist "backend\data" mkdir "backend\data"

if exist "backend\data\gestion_basica.db" (
    echo [INFO] La base de datos YA EXISTE (backend\data\gestion_basica.db).
    echo [INFO] Omitiendo inicializacion de esquema para no sobrescribir.
) else (
    echo [INFO] Inicializando esquema de Base de Datos...
    call backend\venv\Scripts\python.exe backend\scripts\init_db_schema.py backend\data\gestion_basica.db
    if %errorlevel% neq 0 (
        echo [ERROR] Fallo al inicializar DB.
        pause
        exit /b
    )
    echo [OK] Base de Datos inicializada.
)

REM 4. Cargar Datos de Prueba (Opcional)
echo.
:ASK_SEED
set /p DUMMY="¿Desea cargar DATOS DE EJEMPLO? (Esto borrara datos existentes) (S/N): "
if /i "%DUMMY%"=="S" goto :RUN_SEED
if /i "%DUMMY%"=="N" goto :SKIP_SEED
echo [WARN] Por favor responde S o N.
goto :ASK_SEED

:RUN_SEED
echo [INFO] Cargando datos semilla...
call backend\venv\Scripts\python.exe backend\scripts\seed_data_v2.py
if %errorlevel% equ 0 (
    echo [OK] Datos cargados exitosamente.
) else (
    echo [ERROR] Hubo un problema cargando datos.
)
goto :FINISH

:SKIP_SEED
echo [INFO] Saltando carga de datos.

:FINISH

echo.
echo ===================================================
echo   CONFIGURACION COMPLETADA
echo   Ahora puedes ejecutar start_app.bat
echo ===================================================
pause
endlocal
