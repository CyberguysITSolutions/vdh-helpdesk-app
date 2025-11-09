# Quick DB connection + table existence test for fleet/procurement
# Save at the repo root and run it from your activated venv.
import traceback
from fleet import fleet_db

def test_conn_and_tables():
    try:
        print("Calling fleet_db.get_conn()...")
        conn = fleet_db.get_conn()
        print("Connection object type:", type(conn))
        cur = conn.cursor()
        # List up to 20 tables to show DB contents
        cur.execute("""
            SELECT TOP (20) TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE='BASE TABLE'
        """)
        rows = cur.fetchall()
        print("First up to 20 tables (schema, name):")
        for r in rows:
            print(r)
        # Try procurement core table check (adjust table name if different)
        try:
            cur.execute("SELECT TOP (1) * FROM dbo.vehicles")
            sample = cur.fetchone()
            print("Sample row from dbo.vehicles:", sample)
        except Exception as e:
            print("dbo.vehicles query failed; table may be missing or name differs:", e)
        conn.close()
    except Exception:
        print("Full traceback for connection attempt:")
        traceback.print_exc()

if __name__ == '__main__':
    test_conn_and_tables()
