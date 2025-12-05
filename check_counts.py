import os
try:
    import pyodbc
except Exception as e:
    raise SystemExit("pyodbc not installed or unavailable: " + str(e))

server = os.getenv("DB_SERVER")
database = os.getenv("DB_DATABASE")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")

print("DB_SERVER:", server)
print("DB_DATABASE:", database)
print("DB_USERNAME:", username)

conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER=tcp:{server},1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;"
try:
    conn = pyodbc.connect(conn_str, autocommit=True, timeout=60)
    cur = conn.cursor()
    for q in ["SELECT COUNT(*) FROM dbo.Tickets", "SELECT COUNT(*) FROM dbo.Procurement_Requests"]:
        try:
            cur.execute(q)
            print(q, cur.fetchone()[0])
        except Exception as e:
            print("Query failed:", q, e)
    cur.close()
    conn.close()
except Exception as e:
    print("DB connect failed:", e)