#!/usr/bin/env python3
import os, pyodbc, sys, traceback

def main():
    print("pyodbc drivers:", pyodbc.drivers())

    conn_env = os.getenv("DB_CONN")
    if conn_env:
        print("Using DB_CONN environment variable (full connection string)")
        try:
            conn = pyodbc.connect(conn_env, autocommit=True, timeout=10)
            print("Connected using DB_CONN OK")
            conn.close()
            return 0
        except Exception as e:
            print("DB_CONN connect failed:", repr(e))
            traceback.print_exc()
            return 2

    # Fallback to DB_SERVER/DB_DATABASE etc.
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_DATABASE") or os.getenv("DB_NAME")
    user = os.getenv("DB_USERNAME") or os.getenv("DB_USER")
    pwd = os.getenv("DB_PASSWORD") or os.getenv("DB_PASS")
    encrypt = os.getenv("DB_ENCRYPT", "no")
    trust_cert = os.getenv("DB_TRUST_SERVER_CERT", "yes")

    if not server or not database:
        print("DB_SERVER or DB_DATABASE not set. Please set DB_CONN or the DB_* secrets.")
        return 3

    drivers = pyodbc.drivers()
    driver = None
    for preferred in ("ODBC Driver 18 for SQL Server", "ODBC Driver 17 for SQL Server", "SQL Server"):
        if preferred in drivers:
            driver = preferred
            break
    if not driver and drivers:
        driver = drivers[0]

    if not driver:
        print("No ODBC drivers found. msodbcsql may not be installed on the runner.")
        return 4

    if user and pwd:
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={user};PWD={pwd};Encrypt={encrypt};TrustServerCertificate={trust_cert}"
    else:
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;Encrypt={encrypt};TrustServerCertificate={trust_cert}"

    print("Attempting connection with driver:", driver)
    try:
        conn = pyodbc.connect(conn_str, autocommit=True, timeout=10)
        print("Connected OK")
        conn.close()
        return 0
    except Exception as e:
        print("Connection failed:", repr(e))
        traceback.print_exc()
        return 5

if __name__ == "__main__":
    rc = main()
    sys.exit(rc)