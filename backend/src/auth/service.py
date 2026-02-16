
import sqlite3
import pandas as pd
from src.database.db import get_connection
from src.auth.security import get_password_hash

def obtener_usuario_por_username(username_or_hash):
    """
    Busca usuario por username (legacy) o username_hash (nuevo).
    Si se pasa un hash, se asume que es la clave de búsqueda.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        # Try finding by hash first, then by plain username
        cursor.execute("SELECT * FROM users WHERE username_hash = ? OR username = ?", (username_or_hash, username_or_hash))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()

# Alias for internal use (e.g. by security.py) to avoid confusion
obtener_usuario_por_username_internal = obtener_usuario_por_username

def crear_usuario(username, password, role='user', username_hash=None, username_encrypted=None):
    conn = get_connection()
    try:
        pwd_hash = get_password_hash(password)
        conn.execute("""
            INSERT INTO users (username, password_hash, role, username_hash, username_encrypted) 
            VALUES (?, ?, ?, ?, ?)
        """, (username, pwd_hash, role, username_hash, username_encrypted))
        conn.commit()
        return True, "Usuario creado"
    except sqlite3.IntegrityError:
        return False, "Nombre de usuario ya existe"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def listar_usuarios():
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT id, username, role, is_active, created_at, username_encrypted FROM users", conn)
        return df
    finally:
        conn.close()

def eliminar_usuario(user_id):
    conn = get_connection()
    try:
        # Prevent deleting the last admin? maybe later.
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True, "Usuario eliminado"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
