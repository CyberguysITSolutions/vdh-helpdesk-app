# === START: Add these blocks into helpdesk_app.py ===
# 1) Top-level imports (add near other imports)
# Top-level imports (ensure streamlit is imported before any use of `st`)
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import logging
import logging
import pyodbc
logger = logging.getLogger(__name__)
# other imports...

# 2) DB connection helper (add after imports)
def get_db_connection():
    """
    Returns a pyodbc.Connection. Priority:
      1) Use full connection string from DB_CONN env var
      2) Build DSN-less connection from DB_DRIVER/DB_SERVER/DB_NAME/DB_USER/DB_PASS
    Set DB_CONN locally or in App Settings for deployments.
    """
    conn_str = os.getenv("DB_CONN")
    if conn_str:
        try:
            return pyodbc.connect(conn_str, autocommit=True)
        except Exception:
            logger.exception("DB_CONN connect failed, falling back to built string")

    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    server = os.getenv("DB_SERVER", "localhost")
    database = os.getenv("DB_NAME", "mydb")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")

    if user and password:
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};UID={user};PWD={password};Encrypt=no"
    else:
        conn_str = f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};Trusted_Connection=yes;Encrypt=no"

    try:
        return pyodbc.connect(conn_str, autocommit=True)
    except Exception:
        logger.exception("Failed to connect to DB using built connection string")
        raise

# 3) Sidebar menu (replace or merge with existing menu creation)
menu_options = [
    "Dashboard",
    "Tickets",
    "Assets",
    "Procurement",
    "Reports",
    "Users",
    "Fleet Management",     # <-- NEW
    "Query Builder",
    "Connection Test"
]

selection = st.sidebar.selectbox("Navigate", menu_options, index=0)

# 4) Fleet selection wiring (place near other selection handlers)
if selection == "Fleet Management":
    st.header("Fleet Management — debug mode")
    st.write("Debug: entering Fleet selection handler")

    # 1) Confirm module is importable
    try:
        import importlib
        fleet_spec = importlib.util.find_spec("fleet.ui")
        st.write("fleet.ui module found:", bool(fleet_spec))
    except Exception as e:
        st.error("Error checking fleet.ui importability")
        st.exception(e)
        fleet_spec = None

    # 2) Lazy import and inspect
    fleet_ui = None
    if fleet_spec:
        try:
            from fleet import ui as fleet_ui
            st.write("fleet.ui imported:", fleet_ui is not None)
            st.write("Attributes on fleet.ui:", [a for a in dir(fleet_ui) if not a.startswith("_")][:30])
            has_show = hasattr(fleet_ui, "show_fleet_page")
            st.write("fleet_ui has show_fleet_page():", has_show)
        except Exception as e:
            st.error("Import error when importing fleet.ui")
            st.exception(e)
            fleet_ui = None

    # 3) DB quick-test (only if DB config present)
    try:
        from your_module_where_execute_query_lives import execute_query  # adjust if function name / location differs
    except Exception:
        # If your app uses execute_query in top-level, import it from the current module
        try:
            execute_query  # noqa: F821
        except NameError:
            execute_query = None

    if execute_query:
        st.write("execute_query is available")
        try:
            # small harmless query to validate connection, adjust table name if needed
            df, err = execute_query("SELECT TOP 1 1 as ok")
            if err:
                st.warning("DB test returned error: " + str(err))
            else:
                st.success("DB test ok, returned rows: " + str(len(df) if df is not None else 0))
        except Exception as e:
            st.error("DB test raised exception")
            st.exception(e)
    else:
        st.info("No execute_query function available for DB test")

    # 4) Call the page function (if present) and surface any exception
    if fleet_ui and hasattr(fleet_ui, "show_fleet_page"):
        try:
            # If your fleet UI expects a connection object rather than calling execute_query itself,
            # you can pass None for now to test rendering, or create a connection and pass it in.
            try:
                conn = None
                # If your code expects a pyodbc connection, uncomment and adapt:
                # conn = get_db_connection()   # if you have get_db_connection defined and working
            except Exception as e:
                st.warning("Could not create conn object for fleet_ui (continuing with conn=None)")
                st.exception(e)
                conn = None

            fleet_ui.show_fleet_page(conn)
            st.success("fleet_ui.show_fleet_page returned without error")
        except Exception as e:
            st.error("fleet_ui.show_fleet_page raised an exception")
            st.exception(e)
    else:
        st.info("fleet_ui.show_fleet_page not available; please confirm function name and file path.")
# --- end debug block ---
# === END: Add these blocks ===
