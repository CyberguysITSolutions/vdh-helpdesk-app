import os
import traceback

try:
    import pyodbc
except Exception as e:
    raise SystemExit("pyodbc is required for this check: " + str(e))

def get_connection_string():
    # copy the same lookup logic as the app
    try:
        import streamlit as st
        server = st.secrets["database"]["server"]
        database = st.secrets["database"]["database"]
        username = st.secrets["database"]["username"]
        password = st.secrets["database"]["password"]
    except Exception:
        server = os.getenv("DB_SERVER")
        database = os.getenv("DB_DATABASE")
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
    return server, database, username, password

server, database, username, password = get_connection_string()
print("DB_SERVER:", server)
print("DB_DATABASE:", database)
print("DB_USERNAME:", username)

if not all([server, database, username, password]):
    print("Missing DB credentials. Set .streamlit/secrets.toml or environment variables DB_SERVER, DB_DATABASE, DB_USERNAME, DB_PASSWORD")
    raise SystemExit(1)

driver = "ODBC Driver 18 for SQL Server"
conn_str = (
    f"DRIVER={{{driver}}};SERVER=tcp:{server},1433;DATABASE={database};UID={username};PWD={password};"
    "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;Login Timeout=30;"
)
try:
    conn = pyodbc.connect(conn_str, autocommit=True, timeout=30)
    cur = conn.cursor()
    queries = {
        "count_tickets": "SELECT COUNT(*) AS total_tickets FROM dbo.Tickets;",
        "sample_tickets": "SELECT TOP 10 * FROM dbo.Tickets ORDER BY created_at DESC;",
        "count_proc": "SELECT COUNT(*) AS total_proc FROM dbo.Procurement_Requests;",
        "sample_proc": "SELECT TOP 10 * FROM dbo.Procurement_Requests ORDER BY created_at DESC;"
    }
    for name, q in queries.items():
        print("\n---", name, "---")
        try:
            cur.execute(q)
            cols = [c[0] for c in cur.description] if cur.description else []
            rows = cur.fetchmany(10)
            print("cols:", cols)
            print("rows:", rows if rows else "NO ROWS")
        except Exception as e:
            print("Query failed:", e)
            traceback.print_exc()
    cur.close()
    conn.close()
except Exception as e:
    print("DB connect failed:", e)
    traceback.print_exc()