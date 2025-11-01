# test_db.py
import os, pyodbc, sys

print("pyodbc drivers:", pyodbc.drivers())

# If you prefer, set DB_CONN env var to a full DSN-less string before running the script.
conn_env = os.getenv("DB_CONN")
if conn_env:
    print("Using DB_CONN env var")
    try:
        conn = pyodbc.connect(conn_env, autocommit=True, timeout=10)
        print("Connected using DB_CONN OK")
        conn.close()
        sys.exit(0)
    except Exception as e:
        print("DB_CONN connect failed:", repr(e))
        sys.exit(2)

# Otherwise, require explicit DB_SERVER/DB_DATABASE and optional username/password
server = os.getenv("DB_SERVER")
database = os.getenv("DB_DATABASE") or os.getenv("DB_NAME")
user = os.getenv("DB_USERNAME") or os.getenv("DB_USER")
pwd = os.getenv("DB_PASSWORD") or os.getenv("DB_PASS")

if not server or not database:
    print("DB_SERVER or DB_DATABASE not set")
    sys.exit(3)

# choose driver
drivers = pyodbc.drivers()
driver = None
for preferred in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"):
    if preferred in drivers:
        driver = preferred
        break
if not driver and drivers:
    driver = drivers[0]

if not driver:
    print("No ODBC drivers found. Install Microsoft ODBC Driver for SQL Server.")
    sys.exit(4)

if user and pwd:
    conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={user};PWD={pwd};Encrypt=no"
else:
    conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;Encrypt=no"

print("Attempting connection with driver:", driver)
try:
    conn = pyodbc.connect(conn_str, autocommit=True, timeout=10)
    print("Connected OK")
    conn.close()
    sys.exit(0)
except Exception as e:
    print("Connection failed:", repr(e))
    sys.exit(5)
