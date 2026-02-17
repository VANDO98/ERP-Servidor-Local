# Guía de Respaldos en la Nube con Rclone

Esta guía detalla cómo configurar e implementar copias de seguridad automáticas hacia Google Drive (o cualquier otro servicio de nube) utilizando **Rclone**, una herramienta de consola potente y ligera.

## 1. Requisitos Previos
1. Descarga el ejecutable de Rclone para Windows (64 bits) desde [rclone.org](https://rclone.org/downloads/).
2. Extrae el archivo `rclone.exe` en una carpeta permanente, por ejemplo: `C:\rclone\`.

## 2. Configuración del Acceso (Google Drive)
Realiza este proceso una sola vez para autorizar a tu computadora a subir archivos a tu cuenta.

1. Abre una terminal (CMD o PowerShell) y ejecuta:
   ```bash
   C:\rclone\rclone.exe config
   ```
2. Sigue el asistente interactivo:
   - **n)** New remote.
   - **name:** `google_erp` (puedes elegir otro nombre, pero recuérdalo).
   - **Storage:** Selecciona el número correspondiente a **Google Drive**.
   - **client_id / client_secret:** Deja en blanco (Enter).
   - **scope:** Selecciona la opción **1** (Full access).
   - **service_account_file:** Deja en blanco (Enter).
   - **Edit advanced config:** **n** (No).
   - **Use auto config:** **y** (Sí). *Se abrirá tu navegador para loguearte con Google.*
   - **Configure as a Shared Drive?** **n** (No).
   - **Keep this "google_erp" remote?** **y** (Sí).

## 3. Script de Automatización (.bat)
He creado un script sugerido en la carpeta `scripts/nube_backup.bat` (o puedes crearlo tú) con el siguiente contenido:

```batch
@echo off
set "PROJECT_ROOT=C:\Ruta\A\Tu\Proyecto"
cd /d "%PROJECT_ROOT%"

echo [!] Iniciando transferencia a Google Drive...

:: Comando de Rclone para copiar la DB
:: Sintaxis: rclone copy "archivo_local" nombre_remoto:CarpetaEnNube/
C:\rclone\rclone.exe copy "backend\data\gestion_basica.db" google_erp:Backups_ERP/

if %ERRORLEVEL% EQU 0 (
    echo [OK] Base de datos sincronizada con éxito.
) else (
    echo [ERROR] Hubo un problema al conectar con la nube.
)
timeout /t 10
```

## 4. Programación Automática
Para que no tengas que hacerlo manualmente, usa el **Programador de Tareas de Windows**:

1. Busca y abre el "Programador de Tareas".
2. Haz clic en "Crear Tarea Básica".
3. **Nombre:** "Respaldo ERP Nube".
4. **Desencadenador:** Diariamente (selecciona una hora donde la PC esté encendida, ej. 20:00).
5. **Acción:** Iniciar un programa.
6. **Programa/script:** Busca tu archivo `nube_backup.bat`.
7. **Iniciar en:** (CRÍTICO) Pones la ruta completa de la carpeta raíz de tu ERP.

## 5. Ventajas de este Método
- **Historial:** Puedes cambiar el comando a `rclone copy` con fechas en el nombre para tener versiones históricas.
- **Gratuito:** No requiere suscripciones adicionales mas allá de tu cuenta de Google.
- **Invisible:** Corre en segundo plano sin interrumpir el uso del sistema.
