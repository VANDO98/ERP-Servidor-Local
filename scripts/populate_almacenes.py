import sqlite3
import os

DB_PATH = os.path.join("05_Gestion_Basica", "data", "gestion_basica.db")

def populate():
    if not os.path.exists(DB_PATH):
        # Try local path if running from subdir
        DB_PATH_ALT = os.path.join("data", "gestion_basica.db")
        if os.path.exists(DB_PATH_ALT):
            conn = sqlite3.connect(DB_PATH_ALT)
        else:
            print(f"DB not found at {DB_PATH}")
            return
    else:
        conn = sqlite3.connect(DB_PATH)
        
    cursor = conn.cursor()
    
    almacenes = [
        ("Almacén Principal", "Sede Central"),
        ("Sucursal Norte", "Av. Norte 123"),
        ("Sucursal Sur", "Carretera Sur Km 40"),
        ("Depósito Lince", "Jr. Risso 456")
    ]
    
    print("Populating 'almacenes'...")
    for nombre, ubicacion in almacenes:
        try:
            cursor.execute("INSERT INTO almacenes (nombre, ubicacion) VALUES (?, ?)", (nombre, ubicacion))
            print(f"✅ Added: {nombre}")
        except sqlite3.IntegrityError:
            print(f"⚠️ Already exists: {nombre}")
            
    conn.commit()
    
    # Verify
    rows = cursor.execute("SELECT * FROM almacenes").fetchall()
    print("\nCurrent Almacenes:")
    for r in rows:
        print(r)
        
    conn.close()

if __name__ == "__main__":
    populate()
