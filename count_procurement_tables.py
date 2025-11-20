# Quick counts for procurement/fleet tables - run from your activated venv
import traceback
from fleet import fleet_db

tables_to_check = [
    "Procurement_Approvers",
    "Procurement_Requests",
    "Procurement_Items",
    "Procurement_Codes",
    "Procurement_Notes",
    "vehicles"
]

def run_counts():
    try:
        conn = fleet_db.get_conn()
        cur = conn.cursor()
        for t in tables_to_check:
            try:
                cur.execute(f"SELECT COUNT(1) FROM dbo.{t}")
                c = cur.fetchone()[0]
                print(f"{t}: {c}")
            except Exception as e:
                print(f"{t}: ERROR ({e})")
        conn.close()
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    run_counts()