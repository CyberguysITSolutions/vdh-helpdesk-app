# ----- Add / paste these blocks into helpdesk_app.py -----
# 1) Imports (near other top-level imports)
import os
import pyodbc
import logging

logger = logging.getLogger(__name__)

# 2) DB connection helper (use DB_CONN env var if present; otherwise build DSN-less string)
def get_db_connection():
    """
    Return a pyodbc.Connection.
    Priority:
    1) Use exact connection string from env DB_CONN
    2) Build DSN-less connection from DB_DRIVER, DB_SERVER, DB_NAME, DB_USER, DB_PASS
    Ensure you set the env vars locally / in App Settings.
    """
    conn_str = os.getenv("DB_CONN")
    if conn_str:
        try:
            return pyodbc.connect(conn_str, autocommit=True)
        except Exception:
            logger.exception("DB_CONN failed, falling back to built connection string")

    # Fallback: build DSN-less connection string
    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    server = os.getenv("DB_SERVER", "localhost")
    database = os.getenv("DB_NAME", "mydb")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")

    if user and password:
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={user};PWD={password};Encrypt=no"
    else:
        # Trusted connection if no credentials provided
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;Encrypt=no"

    try:
        return pyodbc.connect(conn_str, autocommit=True)
    except Exception as e:
        logger.exception("Failed to connect to DB using built connection string")
        raise

# 3) Navigation: ensure 'Fleet Management' is in your sidebar menu and calls the fleet UI
# Find your existing menu_options or replace the menu construction with this block (below).
menu_options = [
    "Dashboard",
    "Tickets",
    "Assets",
    "Procurement",
    "Reports",
    "Users",
    "Fleet Management",     # <-- added
    "Query Builder",
    "Connection Test"
]

# Re-use your existing selection variable or create a new selectbox:
selection = st.sidebar.selectbox("Navigate", menu_options, index=0)

# When user selects Fleet Management, import & show fleet UI (pass db connection)
if selection == "Fleet Management":
    # keep import here to avoid importing fleet code when not needed
    try:
        from fleet import ui as fleet_ui
    except Exception:
        st.error("Fleet module not found. Ensure fleet/ui.py exists in the repo and exports show_fleet_page().")
    else:
        try:
            conn = get_db_connection()
        except Exception:
            st.error("Unable to connect to database. Check DB_CONN or DB_* env vars and installed ODBC driver.")
        else:
            # Expect fleet_ui.show_fleet_page(conn) to exist; adjust if the API is different
            fleet_ui.show_fleet_page(conn)
# ----- end of snippet -----
