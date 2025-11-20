import sys
from fleet import fleet_db

def run():
    conn = fleet_db.get_conn()
    cur = conn.cursor()

    print("Columns in dbo.vehicles (name, type):")
    cur.execute("""
        SELECT COLUMN_NAME, DATA_TYPE, ORDINAL_POSITION, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='vehicles'
        ORDER BY ORDINAL_POSITION
    """)
    for row in cur.fetchall():
        print(row)

    print("\nPrimary key columns for dbo.vehicles:")
    cur.execute("""
        SELECT kcu.COLUMN_NAME
        FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
        JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
          ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME
        WHERE tc.TABLE_SCHEMA = 'dbo' AND tc.TABLE_NAME = 'vehicles' AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
        ORDER BY kcu.ORDINAL_POSITION
    """)
    pk_rows = cur.fetchall()
    if pk_rows:
        for r in pk_rows:
            print(r[0])
    else:
        print("No primary key found (unexpected).")

    cur.close()
    conn.close()

if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        print("Error:", e)
        sys.exit(1)