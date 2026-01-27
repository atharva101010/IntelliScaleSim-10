import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

# Show container table structure
cursor.execute("PRAGMA table_info(container)")
print("\nContainer table columns:")
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

conn.close()
