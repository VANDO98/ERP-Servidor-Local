
@echo off
setlocal enabledelayedexpansion

:: --- CONFIGURATION ---
set "SOURCE_DB=backend\data\gestion_basica.db"
set "BACKUP_DIR=backups"
set "MAX_BACKUPS=7"

:: Get current date/time for filename
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set "DATE=%%c%%a%%b"
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set "TIME=%%a%%b"
set "FILENAME=backup_auto_%DATE%_%TIME%.db"

echo [!] Iniciando copia de seguridad automatica...

:: Create backup dir if not exists
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:: Perform simple copy (Safe enough if server is not in a heavy write loop)
copy "%SOURCE_DB%" "%BACKUP_DIR%\%FILENAME%" > nul

if %ERRORLEVEL% EQU 0 (
    echo [OK] Copia creada: %BACKUP_DIR%\%FILENAME%
) else (
    echo [ERROR] No se pudo crear la copia de seguridad.
    pause
    exit /b 1
)

:: Cleanup old backups (keep last N)
echo [!] Limpiando copias antiguas...
for /f "skip=%MAX_BACKUPS% delims=" %%F in ('dir "%BACKUP_DIR%\backup_auto_*.db" /b /o-d') do (
    del "%BACKUP_DIR%\%%F"
    echo [-] Eliminada copia antigua: %%F
)

echo [OK] Proceso terminado.
timeout /t 5
