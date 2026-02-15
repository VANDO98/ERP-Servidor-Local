import sys
import subprocess
try:
    from importlib.metadata import distributions
except ImportError:
    # Fallback for older python < 3.8, though project requires 3.10+
    try:
        from importlib_metadata import distributions
    except ImportError:
        # Last resort: try pkg_resources
        import pkg_resources
        def distributions():
            return pkg_resources.working_set

REQUIRED_PACKAGES = [
    'fastapi',
    'uvicorn',
    'pandas',
    'openpyxl',
    'python-multipart',
    'requests',
    'pydantic',
    'passlib',
    'bcrypt',
    'python-jose',
    'cryptography',
    'httpx'
]

def check_and_install():
    try:
        # Get installed packages (normalized names)
        # Note: distributions() returns objects with .metadata attribute
        # We handle both importlib.metadata and pkg_resources styles if mixed, 
        # but importlib.metadata is standard in 3.10+
        if 'pkg_resources' in sys.modules and distributions == pkg_resources.working_set:
             installed = {pkg.key.lower() for pkg in distributions()}
        else:
             installed = {dist.metadata['Name'].lower() for dist in distributions()}
            
    except Exception as e:
        print(f"[WARN] Error verificando librerias con metodo estandar: {e}")
        print("Intentando instalacion forzada de requirements...")
        installed = set()

    # Check missing (simple check)
    missing = [pkg for pkg in REQUIRED_PACKAGES if pkg.lower() not in installed]

    if missing:
        print(f"Instalando librerias faltantes: {', '.join(missing)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])
            print("Instalacion completada exitosamente.")
        except subprocess.CalledProcessError as e:
            print(f"Error al instalar librerias: {e}")
            sys.exit(1)
    else:
        print("Todas las librerias necesarias estan instaladas.")

if __name__ == "__main__":
    check_and_install()
