"""
Run a few diagnostic queries (same DB helper the Streamlit app uses)
and print results, column names and Python types so we can spot
unsupported/odd types (e.g., DATETIMEOFFSET) or empty results.

Run with:
  .venv\Scripts\python.exe test_db_queries.py
"""

import traceback
import pandas as pd

def run_query(q, params=None):
    try:
        from fleet import fleet_db
    except Exception as e:
        print("ERROR: could not import fleet.fleet_db:", e)
        return
    try:
        conn = fleet_db.get_conn()
    except Exception as e:
        print("ERROR: could not get DB connection from fleet.fleet_db.get_conn():", e)
        return

    try:
        if params:
            df = pd.read_sql(q, conn, params=params)
        else:
            df = pd.read_sql(q, conn)
    except Exception as e:
        print("Query execution / fetch error:")
        print(e)
        print(traceback.format_exc())
        try:
            conn.close()
        except:
            pass
        return

    try:
        print("="*80)
        print("Query:")
        print(q)
        print("- result shape:", None if df is None else df.shape)
        if df is None or len(df) == 0:
            print("No rows returned.")
        else:
            # Show up to 5 rows
            print("\nFirst rows (up to 5):")
            print(df.head(5).to_string(index=False))
            print("\nColumn names and dtypes (pandas dtype):")
            print(df.dtypes)
            # Show Python types of first row values for columns (to spot e.g. object->pyodbc/ODBC types)
            print("\nPython types of first row values:")
            first = df.iloc[0]
            for col in df.columns:
                val = first[col]
                print(f" - {col!r}: value={repr(val)}  type={type(val)}")
    except Exception as e:
        print("Error printing results:", e)
        print(traceback.format_exc())
    finally:
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    # Replace these queries with the ones used by your pages if necessary.
    queries = {
        "Tickets_sample": "SELECT TOP (5) * FROM dbo.Tickets ORDER BY ticket_id DESC",
        "Assets_sample": "SELECT TOP (5) * FROM dbo.Assets ORDER BY id DESC",
        "Procurement_requests_sample": "SELECT TOP (5) * FROM dbo.Procurement_Requests ORDER BY request_id DESC",
        "Vehicle_Trips_sample": "SELECT TOP (5) * FROM dbo.Vehicle_Trips ORDER BY trip_id DESC",
    }

    for name, q in queries.items():
        print("\n\nDIAGNOSTIC:", name)
        run_query(q)