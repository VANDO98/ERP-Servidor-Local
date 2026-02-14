import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== Creando Admin Manualmente ===\n")

# Generar hash sin usar passlib
try:
    import bcrypt
    password = b"admin"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    hashed_str = hashed.decode('utf-8')
    print(f"✅ Hash generado: {hashed_str[:20]}...")
    
    # Insertar en DB
    from src.backend import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si ya existe
    cursor.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if cursor.fetchone()[0] > 0:
        print("⚠️  Admin ya existe, eliminando...")
        cursor.execute("DELETE FROM users WHERE username='admin'")
        conn.commit()
    
    # Insertar nuevo admin
    cursor.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        ("admin", hashed_str, "admin")
    )
    conn.commit()
    print("✅ Admin creado exitosamente")
    
    # Verificar
    cursor.execute("SELECT username, role FROM users WHERE username='admin'")
    admin = cursor.fetchone()
    print(f"✅ Verificación: {admin}")
    
    conn.close()
    
    # Probar verificación
    print("\n=== Probando Verificación ===")
    is_valid = bcrypt.checkpw(b"admin", hashed)
    print(f"✅ Password válido: {is_valid}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
