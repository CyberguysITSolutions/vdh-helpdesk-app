# seed_minimal_procurement.py
# Safe minimal seeding for vehicles and Procurement_Items (only inserts if tables empty).
# Run from repo root with your venv active:
# python seed_minimal_procurement.py
import traceback
from decimal import Decimal
from fleet import fleet_db

def is_identity(cur, table: str, column: str) -> bool:
    cur.execute(
        "SELECT COLUMNPROPERTY(OBJECT_ID(?), ?, 'IsIdentity')",
        (f"dbo.{table}", column),
    )
    r = cur.fetchone()
    return bool(r and r[0] == 1)

def count_rows(cur, table: str) -> int:
    cur.execute(f"SELECT COUNT(1) FROM dbo.{table}")
    return cur.fetchone()[0]

def get_any_request_id(cur):
    cur.execute("SELECT TOP (1) request_id FROM dbo.Procurement_Requests ORDER BY request_id")
    r = cur.fetchone()
    return r[0] if r else None

def insert_vehicle(cur):
    # Minimal insert: supply required make_model; other required columns have defaults.
    cur.execute("INSERT INTO dbo.vehicles (make_model) VALUES (?)", ("Initial Vehicle (seed)",))

def insert_procurement_item(cur, request_id):
    # Minimal insert: request_id, line_number, item_description, unit_price (quantity has default)
    cur.execute(
        "INSERT INTO dbo.Procurement_Items (request_id, line_number, item_description, unit_price) VALUES (?, ?, ?, ?)",
        (request_id, 1, "Initial procurement item (seed)", Decimal("1.00")),
    )

def main():
    try:
        conn = fleet_db.get_conn()
        cur = conn.cursor()

        # VEHICLES
        print("Checking vehicles table...")
        try:
            v_count = count_rows(cur, "vehicles")
            print("vehicles count before:", v_count)
        except Exception as e:
            print("Error counting vehicles:", e)
            traceback.print_exc()
            conn.close()
            return

        if v_count == 0:
            print("vehicles is empty. Preparing to insert a seed row...")
            try:
                ident = is_identity(cur, "vehicles", "id")
            except Exception:
                # If identity check fails, assume identity False and proceed to compute id if necessary
                ident = False
            print("vehicles.id is identity:", ident)

            try:
                if ident:
                    insert_vehicle(cur)
                else:
                    # compute next id
                    cur.execute("SELECT ISNULL(MAX(id), 0) + 1 FROM dbo.vehicles")
                    next_id = cur.fetchone()[0]
                    cur.execute(
                        "INSERT INTO dbo.vehicles (id, make_model, initial_mileage, current_mileage, miles_until_service, status) VALUES (?, ?, ?, ?, ?, ?)",
                        (next_id, "Initial Vehicle (seed)", 0, 0, 4000, "motorpool"),
                    )
                conn.commit()
                v_count_after = count_rows(cur, "vehicles")
                print("vehicles count after:", v_count_after)
            except Exception:
                print("Failed to insert into vehicles:")
                traceback.print_exc()
                conn.rollback()
        else:
            print("vehicles already has rows; skipping insert.")

        # PROCUREMENT ITEMS
        print("\nChecking Procurement_Items table...")
        try:
            p_count = count_rows(cur, "Procurement_Items")
            print("Procurement_Items count before:", p_count)
        except Exception as e:
            print("Error counting Procurement_Items:", e)
            traceback.print_exc()
            conn.close()
            return

        if p_count == 0:
            print("Procurement_Items is empty. Preparing to insert a seed row...")
            try:
                request_id = get_any_request_id(cur)
                if request_id is None:
                    raise RuntimeError("No Procurement_Requests found; cannot insert Procurement_Items without a request.")
                print("Using request_id:", request_id)

                ident = is_identity(cur, "Procurement_Items", "item_id")
                print("Procurement_Items.item_id is identity:", ident)

                if ident:
                    insert_procurement_item(cur, request_id)
                else:
                    cur.execute("SELECT ISNULL(MAX(item_id), 0) + 1 FROM dbo.Procurement_Items")
                    next_item_id = cur.fetchone()[0]
                    cur.execute(
                        "INSERT INTO dbo.Procurement_Items (item_id, request_id, line_number, item_description, quantity, unit_price) VALUES (?, ?, ?, ?, ?, ?)",
                        (next_item_id, request_id, 1, "Initial procurement item (seed)", 1, Decimal("1.00")),
                    )
                conn.commit()
                p_count_after = count_rows(cur, "Procurement_Items")
                print("Procurement_Items count after:", p_count_after)
            except Exception:
                print("Failed to insert into Procurement_Items:")
                traceback.print_exc()
                conn.rollback()
        else:
            print("Procurement_Items already has rows; skipping insert.")

        cur.close()
        conn.close()
        print("\nSeeding script complete.")
    except Exception:
        print("Unexpected failure:")
        traceback.print_exc()

if __name__ == "__main__":
    main()