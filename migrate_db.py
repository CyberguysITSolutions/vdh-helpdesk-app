"""
migrate_db.py

Run the SQL migration script against the database using fleet.fleet_db.get_conn().

Usage:
  ".venv\\Scripts\\python.exe" migrate_db.py

This will execute the SQL file sql_migrations/add_fleet_trips_and_fields.sql.
"""
import os
import sys

SQL_PATH = os.path.join("sql_migrations", "add_fleet_trips_and_fields.sql")

def run_script():
    try:
        from fleet import fleet_db
    except Exception as e:
        print("Error: could not import fleet.fleet_db:", e)
        sys.exit(1)

    try:
        conn = fleet_db.get_conn()
    except Exception as e:
        print("Error: could not connect to DB using fleet_db.get_conn():", e)
        sys.exit(1)

    if not os.path.exists(SQL_PATH):
        print("Migration SQL not found at", SQL_PATH)
        sys.exit(1)

    with open(SQL_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    # Split on GO lines into batches
    batches = []
    batch_lines = []
    for line in sql.splitlines():
        if line.strip().upper() == "GO":
            if batch_lines:
                batches.append("\n".join(batch_lines))
                batch_lines = []
        else:
            batch_lines.append(line)
    if batch_lines:
        batches.append("\n".join(batch_lines))

    try:
        cur = conn.cursor()
        for b in batches:
            if b.strip():
                cur.execute(b)
                # consume any additional result sets
                while cur.nextset():
                    pass
        conn.commit()
        cur.close()
        conn.close()
        print("Migration completed successfully.")
    except Exception as e:
        print("Migration failed:", e)
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    run_script()