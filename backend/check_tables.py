import psycopg2

try:
    conn = psycopg2.connect(
        dbname="intelliscalesim",
        user="postgres",
        password="postgres",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    tables = [row[0] for row in cursor.fetchall()]
    print("Tables:", tables)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
