import sqlite3
import os

# Source Database
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
DB_PATH = os.path.join(BASE_DIR, 'data', 'gestion_basica.db')

# Output Script
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'init_db_schema.py')

def export_schema():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    print(f"Reading schema from: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all schema items in correct order? 
    # Tables first, then indices, then triggers.
    # sqlite_master: type, name, tbl_name, rootpage, sql
    
    schema_commands = []
    
    # 1. Tables
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name")
    tables = cursor.fetchall()
    for sql in tables:
        if sql[0]:
            schema_commands.append(sql[0])

    # 2. Indices
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL ORDER BY name")
    indices = cursor.fetchall()
    for sql in indices:
        if sql[0]:
            schema_commands.append(sql[0])

    # 3. Triggers
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND sql IS NOT NULL ORDER BY name")
    triggers = cursor.fetchall()
    for sql in triggers:
        if sql[0]:
            schema_commands.append(sql[0])
            
    conn.close()
    
    # Generate Python Script
    script_content = f"""import sqlite3
import os
import sys

def init_db(db_path):
    if os.path.exists(db_path):
        print(f"Warning: Database already exists at {{db_path}}")
        # Optional: os.remove(db_path) or return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating tables...")
    try:
"""
    
    for sql in schema_commands:
        # Escape quotes if necessary, or use triple quotes
        # We'll use triple quotes for safety
        script_content += f"""        cursor.execute('''{sql}''')\n"""

    script_content += """
        conn.commit()
        print("Database schema initialized successfully.")
    except Exception as e:
        print(f"Error creating schema: {{e}}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python init_db_schema.py <path_to_new_db.db>")
    else:
        init_db(sys.argv[1])
"""

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(script_content)
        
    print(f"Schema script generated at: {OUTPUT_FILE}")

if __name__ == "__main__":
    export_schema()
