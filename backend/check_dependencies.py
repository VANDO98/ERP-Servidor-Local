import sys
import subprocess
try:
    from importlib.metadata import distributions
except ImportError:
    try:
        from importlib_metadata import distributions
    except ImportError:
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
        if 'pkg_resources' in sys.modules and distributions == pkg_resources.working_set:
             installed = {pkg.key.lower() for pkg in distributions()}
        else:
             installed = {dist.metadata['Name'].lower() for dist in distributions()}
            
    except Exception as e:
        print(f"[WARN] Error verificando librerias con metodo estandar: {e}")
        print("Intentando instalacion forzada de requirements...")
        installed = set()

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
