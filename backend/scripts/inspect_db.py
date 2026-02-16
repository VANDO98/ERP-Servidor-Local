import sqlite3
import os

# Adjust path if necessary, but this script will be run from root
db_path = os.path.join("backend", "data", "gestion_basica.db")

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables found:")
for t in tables:
    table_name = t[0]
    if table_name == "sqlite_sequence": continue
    print(f"- {table_name}")
    
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = cursor.fetchall()
    # Format: (cid, name, type, notnull, dflt_value, pk)
    col_names = [f"{c[1]} ({c[2]})" for c in cols]
    print(f"  Columns: {', '.join(col_names)}")

conn.close()
