import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend import get_connection, crear_usuario

print("=== Inspección BD Usuarios ===\n")

# 1. Ver usuarios actuales
conn = get_connection()
cursor = conn.cursor()

try:
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    print(f"Usuarios en DB: {len(users)}")
    for u in users:
        print(f"  - ID: {u[0]}, Username: {u[1]}, Role: {u[3]}")
    
    if len(users) == 0:
        print("\n⚠️  No hay usuarios. Creando admin...")
        conn.close()
        
        # Crear admin
        ok, msg = crear_usuario("admin", "admin", "admin")
        if ok:
            print(f"✅ {msg}")
        else:
            print(f"❌ Error: {msg}")
            
        # Verificar
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users WHERE username='admin'")
        admin = cursor.fetchone()
        if admin:
            print(f"✅ Admin creado: {admin}")
        else:
            print("❌ Admin no se creó correctamente")
    else:
        print("\n✅ Usuarios ya existen")
        
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    conn.close()
