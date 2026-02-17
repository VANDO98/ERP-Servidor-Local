
import os
import shutil
import sqlite3
from datetime import datetime
from src.database.db import DB_PATH, BASE_DIR

# Backup directory relative to project root
BACKUP_DIR = os.path.join(BASE_DIR, "backups")

def create_backup():
    """
    Creates a backup of the main SQLite database using VACUUM INTO for a safe copy.
    """
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.db"
    backup_full_path = os.path.join(BACKUP_DIR, backup_filename)
    
    # Use VACUUM INTO to create a safe copy while the DB might be in use
    conn = sqlite3.connect(DB_PATH)
    try:
        # SQLite 3.27.0+ supports VACUUM INTO
        # If not supported, we fallback to shutil.copy2 (risky if write-heavy)
        conn.execute(f"VACUUM INTO '{backup_full_path}'")
        return True, backup_filename
    except Exception as e:
        print(f"VACUUM INTO failed, trying direct copy: {e}")
        try:
            shutil.copy2(DB_PATH, backup_full_path)
            return True, backup_filename
        except Exception as e2:
            return False, str(e2)
    finally:
        conn.close()

def list_backups():
    """Returns a list of backup files sorted by date (newest first)"""
    if not os.path.exists(BACKUP_DIR):
        return []
        
    files = []
    for f in os.listdir(BACKUP_DIR):
        if f.startswith("backup_") and f.endswith(".db"):
            path = os.path.join(BACKUP_DIR, f)
            stat = os.stat(path)
            files.append({
                "filename": f,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
            
    # Sort by filename descending (which corresponds to timestamp)
    files.sort(key=lambda x: x['filename'], reverse=True)
    return files

def get_backup_path(filename):
    """Returns the absolute path of a backup file if it exists and is secure"""
    # Simple security check to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        return None
        
    path = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(path):
        return path
    return None

def cleanup_old_backups(keep_days=7):
    """Removes backups older than keep_days"""
    if not os.path.exists(BACKUP_DIR):
        return
        
    now = datetime.now().timestamp()
    for f in os.listdir(BACKUP_DIR):
        path = os.path.join(BACKUP_DIR, f)
        if os.path.isfile(path):
            if (now - os.path.getmtime(path)) > (keep_days * 86400):
                os.remove(path)
                print(f"Removed old backup: {f}")
