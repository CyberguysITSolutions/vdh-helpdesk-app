# db_check.py - prints DB server/database and row counts for key tables using fleet.fleet_db
# Run with your venv python:
# ".venv\Scripts\python.exe" db_check.py

import traceback
import pandas as pd

try:
    from fleet import fleet_db
except Exception as e:
    print("Failed to import fleet.fleet_db:", e)
    raise

def try_conn_info():
    try:
        # try to get connection object, then server/database via cursor.connection attributes if available
        conn = fleet_db.get_conn()
        cursor = conn.cursor()
        # Print a simple query to confirm connectivity
        cursor.execute("SELECT DB_NAME() as dbname, @@SERVERNAME as server")
        row = cursor.fetchone()
        print("DB connection OK. Server / Database:", row)
        cursor.close()
        conn.close()
    except Exception:
        traceback.print_exc()

def table_counts():
    tables = [
        "Procurement_Requests",
        "Procurement_Items",
        "Procurement_Approvers",
        "Procurement_Notes",
        "vehicles",
        "Assets",
        "Tickets"
    ]
    try:
        conn = fleet_db.get_conn()
        cur = conn.cursor()
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(1) FROM dbo.{t}")
                cnt = cur.fetchone()[0]
                print(f"{t}: {cnt}")
            except Exception as e:
                print(f"{t}: ERROR - {e}")
        cur.close()
        conn.close()
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Checking DB connection info ===")
    try_conn_info()
    print("\n=== Checking table counts ===")
    table_counts()