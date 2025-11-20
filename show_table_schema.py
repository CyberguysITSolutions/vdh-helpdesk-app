# show_table_schema.py
# Prints column metadata for vehicles and Procurement_Items
from fleet import fleet_db
import traceback

tables = ["vehicles", "Procurement_Items"]

def show():
    try:
        conn = fleet_db.get_conn()
        cur = conn.cursor()
        for t in tables:
            print(f"\nColumns for dbo.{t}:")
            cur.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=?
                ORDER BY ORDINAL_POSITION
            """, (t,))
            rows = cur.fetchall()
            for row in rows:
                print(row)
        conn.close()
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    show()