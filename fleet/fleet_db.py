import pyodbc
import streamlit as st
import time

def _escape_odbc_value(val: str) -> str:
    """Escape an ODBC value by wrapping in braces and doubling '}' if it contains special chars."""
    if val is None:
        return ""
    if any(c in val for c in [';', '{', '}']):
        val_escaped = val.replace('}', '}}')
        return "{" + val_escaped + "}"
    return val

def _choose_driver():
    installed = pyodbc.drivers()
    preferred = ["ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"]
    for p in preferred:
        if p in installed:
            return p
    return installed[0] if installed else None

def get_conn():
    """
    Return a pyodbc connection using st.secrets['database'] with keys:
      - server
      - database
      - username
      - password

    Behavior:
    - chooses an available driver
    - ensures server uses tcp:... ,1433 for Azure SQL
    - escapes password if it contains special characters
    - tries a short strict TLS attempt first, then falls back to a longer timeout and TrustServerCertificate=yes
    """
    db = st.secrets["database"]

    # Validate secrets
    if not db.get("server"):
        raise RuntimeError("st.secrets['database']['server'] is missing")
    if not db.get("database"):
        raise RuntimeError("st.secrets['database']['database'] is missing")
    if not db.get("username") or not db.get("password"):
        raise RuntimeError("st.secrets['database'] must include username and password")

    driver = _choose_driver()
    if not driver:
        raise RuntimeError(f"No ODBC drivers found. Installed drivers: {pyodbc.drivers()}")

    # Normalize server for Azure SQL: ensure tcp: and port 1433
    server = db.get("server")
    if not server.lower().startswith("tcp:") and "," not in server:
        server = f"tcp:{server},1433"

    uid = db.get("username")
    pwd = _escape_odbc_value(db.get("password"))
    database = db.get("database")

    # Ordered variants to try: prefer strict -> fallback to trusted cert and longer timeout
    variants = [
        # strict TLS (preferred for production)
        {"Encrypt": "yes", "TrustServerCertificate": "no", "LoginTimeout": "30"},
        # fallback for environments that fail TLS validation or require longer negotiation time
        {"Encrypt": "yes", "TrustServerCertificate": "yes", "LoginTimeout": "60"},
    ]

    last_exc = None
    for v in variants:
        tail = ";".join(f"{k}={v[k]}" for k in v)
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={uid};"
            f"PWD={pwd};"
            f"{tail};"
        )
        try:
            # Try to connect
            conn = pyodbc.connect(conn_str, autocommit=False)
            return conn
        except Exception as e:
            last_exc = e
            # small pause before retry (helps in transient network cases)
            time.sleep(0.2)

    # If we get here, all attempts failed
    raise last_exc