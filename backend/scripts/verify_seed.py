import sqlite3
import os

db_path = os.path.join("..", "data", "gestion_basica.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Data Verification ---")

# Check Users
cursor.execute("SELECT username, role FROM users")
print("\nUsers:", cursor.fetchall())

# Check Master Data Counts
cursor.execute("SELECT COUNT(*) FROM productos")
print("Productos:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM proveedores")
print("Proveedores:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM categorias")
print("Categorias:", cursor.fetchone()[0])

# Check Transactions
cursor.execute("SELECT COUNT(*) FROM compras_cabecera")
print("Compras:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM salidas_cabecera")
print("Salidas:", cursor.fetchone()[0])

cursor.execute("SELECT COUNT(*) FROM ordenes_compra")
print("Ordenes Compra:", cursor.fetchone()[0])

print("\n--- Top 5 Products by Stock ---")
cursor.execute("SELECT nombre, stock_actual FROM productos ORDER BY stock_actual DESC LIMIT 5")
for r in cursor.fetchall():
    print(f"- {r[0]}: {r[1]}")

conn.close()
