#!/usr/bin/env python3
"""
test_db_connect.py

Interactive connection tester for your Azure SQL / ODBC setup.

- Reads server, database, username from .streamlit/secrets.toml or secrets.toml (if present),
  otherwise falls back to environment variables DB_SERVER, DB_DATABASE, DB_USERNAME.
- Prompts you for the password (securely).
- Tries several driver / encrypt / username variants (ODBC 18/17, username and username@shortserver).
- Runs a simple test query on each successful connection and prints detailed errors for failures.

Place this file in the repo root and run with the venv python:
  ".venv\\Scripts\\python.exe" test_db_connect.py

Do NOT paste your password or any secrets here.
"""
import sys
import os
import getpass
import traceback
import socket

# Try to read toml files (prefer tomllib if available, otherwise toml package)
def load_secrets():
    candidates = [os.path.join(".streamlit", "secrets.toml"), "secrets.toml"]
    data = {}
    toml_loaded = False
    for path in candidates:
        if os.path.exists(path):
            try:
                # Python 3.11+ has tomllib
                try:
                    import tomllib as tomllib
                    with open(path, "rb") as f:
                        data = tomllib.load(f)
                        toml_loaded = True
                        break
                except Exception:
                    # fallback to toml package
                    import toml as tomllib
                    with open(path, "r", encoding="utf-8") as f:
                        data = tomllib.load(f)
                        toml_loaded = True
                        break
            except Exception:
                pass
    return data.get("database", {}) if toml_loaded else {}

def host_shortname(server):
    # for username@shortserver case (Azure style)
    try:
        return server.split(".")[0]
    except Exception:
        return server

def try_connect(conn_str):
    import pyodbc
    try:
        conn = pyodbc.connect(conn_str, timeout=15)
        cur = conn.cursor()
        # simple verification query
        try:
            cur.execute("SELECT DB_NAME() as dbname, @@SERVERNAME as servername")
            row = cur.fetchone()
            cur.close()
            conn.close()
            return True, f"OK - query returned: {row}"
        except Exception as e:
            try:
                cur.close()
            except:
                pass
            conn.close()
            return True, f"Connected, but test query failed: {e}"
    except Exception as e:
        # return False and the exception text
        return False, repr(e)

def main():
    print("\n== DB Connection Tester ==")
    secrets = load_secrets()
    server = secrets.get("server") or os.getenv("DB_SERVER")
    database = secrets.get("database") or os.getenv("DB_DATABASE")
    username = secrets.get("username") or os.getenv("DB_USERNAME")

    print(f"\nDetected connection settings (no password shown):")
    print(f"  server  : {server}")
    print(f"  database: {database}")
    print(f"  username: {username}")

    if not server or not database or not username:
        print("\nWarning: missing server/database/username in secrets or env. You will be prompted for missing values.")
        if not server:
            server = input("Server hostname (e.g. myserver.database.windows.net): ").strip()
        if not database:
            database = input("Database name: ").strip()
        if not username:
            username = input("Username: ").strip()

    pwd = getpass.getpass("\nEnter database password (won't be echoed): ").strip()
    if not pwd:
        print("Password empty; exiting.")
        return

    short = host_shortname(server)
    user_variants = [username]
    # if username doesn't already contain '@', add username@shortserver variant for Azure
    if "@" not in username:
        user_variants.append(f"{username}@{short}")

    drivers = [
        "ODBC Driver 18 for SQL Server",
        "ODBC Driver 17 for SQL Server"
    ]

    encrypt_options = [
        ("Encrypt=yes", "TrustServerCertificate=yes"),
        ("Encrypt=yes", "TrustServerCertificate=no"),
        ("Encrypt=no", "TrustServerCertificate=yes"),
        ("Encrypt=no", "TrustServerCertificate=no")
    ]

    # Build combinations and test them
    results = []
    print("\nTesting combinations (this may take a few seconds per attempt)...\n")

    for drv in drivers:
        for user in user_variants:
            for enc, trust in encrypt_options:
                # Skip nonsensical combos? We'll keep them; driver will fail or succeed.
                conn_str = (
                    f"DRIVER={{{drv}}};"
                    f"SERVER={server};DATABASE={database};"
                    f"UID={user};PWD={pwd};"
                    f"{enc};{trust};"
                    f"Connection Timeout=10;"
                )
                label = f"Driver='{drv}' | User='{user}' | {enc} | {trust}"
                print(f"Trying: {label} ...", end=" ", flush=True)
                ok, message = try_connect(conn_str)
                if ok:
                    print("SUCCESS")
                    print("  ->", message)
                    results.append((label, True, message))
                    # Optionally stop on first success; we'll keep testing to find alternatives
                else:
                    print("FAIL")
                    print("  ->", message)
                    results.append((label, False, message))

    # Summary
    print("\n\n=== Summary ===")
    successes = [r for r in results if r[1]]
    if successes:
        print(f"\nSuccessful connections ({len(successes)}):")
        for s in successes:
            print(" -", s[0])
            print("    ->", s[2])
    else:
        print("\nNo successful connections. Failures:")
        for r in results:
            print(" -", r[0])
            print("    ->", r[2])

    print("\nNext steps if all failed:")
    print(" - Verify Azure SQL firewall allows your client IP (add client IP in Azure Portal).")
    print(" - Confirm username format (Azure often requires username@servername_short).")
    print(" - Try switching drivers (installed ODBC drivers).")
    print(" - If you see 'Login timeout' but Test-NetConnection succeeded, check server firewall or corporate proxy blocking TLS handshake.")
    print("\nRun this file with your venv python, e.g.:")
    print('  ".venv\\Scripts\\python.exe" test_db_connect.py')
    print("\nDone.\n")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)