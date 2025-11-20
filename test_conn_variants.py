# test_conn_variants.py
# Try several ODBC connection-string variants and print detailed exceptions.
import pyodbc
import streamlit as st
import traceback

def escape_odbc_value(val: str) -> str:
    if val is None:
        return ""
    # If value contains semicolon or braces, wrap in braces and double '}' characters
    if any(c in val for c in [';', '{', '}']):
        val_escaped = val.replace('}', '}}')
        return "{" + val_escaped + "}"
    return val

# Read secrets
db = st.secrets["database"]
server = db.get("server", "")
if not server.lower().startswith("tcp:") and "," not in server:
    server = f"tcp:{server},1433"

# choose driver
installed_drivers = pyodbc.drivers()
driver = next((d for d in installed_drivers if "ODBC Driver 18" in d), None)
if not driver:
    driver = installed_drivers[0] if installed_drivers else ""

user = db.get("username")
pwd_raw = db.get("password")
pwd = escape_odbc_value(pwd_raw)
database = db.get("database")

variants = [
    ("Encrypt=yes;TrustServerCertificate=no", "Encrypt=yes;TrustServerCertificate=no"),
    ("Encrypt=yes;TrustServerCertificate=yes", "Encrypt=yes;TrustServerCertificate=yes"),
    ("Encrypt=no;TrustServerCertificate=yes", "Encrypt=no;TrustServerCertificate=yes"),
    ("Encrypt=yes;TrustServerCertificate=yes;LoginTimeout=30", "Encrypt=yes;TrustServerCertificate=yes;LoginTimeout=30"),
    ("Encrypt=yes;TrustServerCertificate=yes;LoginTimeout=60", "Encrypt=yes;TrustServerCertificate=yes;LoginTimeout=60")
]

print("Using driver:", driver)
for label, tail in variants:
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={user};"
        f"PWD={pwd};"
        f"{tail};"
    )
    print("\n=== TRY:", label)
    print("Connection string (masked PWD):", conn_str.replace(pwd, "{*****}"))
    try:
        conn = pyodbc.connect(conn_str, autocommit=False)
        print("Connected OK with variant:", label)
        conn.close()
    except Exception:
        print("Exception for variant:", label)
        traceback.print_exc()