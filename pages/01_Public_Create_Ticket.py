"""
Public Create Ticket page (standalone)

Place this file in the repo under pages/ so Streamlit will treat it as an independent page in the same app.
Supports MOCK_DATA via environment variable MOCK_DATA=1.
"""

import os
import traceback
from datetime import datetime
from typing import Optional, Tuple, Any

import streamlit as st
import pandas as pd

# Try to import pyodbc (optional)
try:
    import pyodbc
    HAS_PYODBC = True
except Exception:
    HAS_PYODBC = False

# Page config
st.set_page_config(page_title="VDH - Public Ticket Submission", page_icon="🎫", layout="centered")

# MOCK / testing mode (set env MOCK_DATA=1 to enable)
MOCK_DATA = os.getenv("MOCK_DATA", "0") == "1"

@st.cache_resource
def get_connection_string():
    try:
        server = st.secrets["database"]["server"]
        database = st.secrets["database"]["database"]
        username = st.secrets["database"]["username"]
        password = st.secrets["database"]["password"]
    except Exception:
        server = os.getenv("DB_SERVER")
        database = os.getenv("DB_DATABASE")
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
    return server, database, username, password


def get_db_connection():
    if MOCK_DATA:
        raise ConnectionError("MOCK_DATA enabled - no DB connection in public_ticket.py")
    if not HAS_PYODBC:
        raise ConnectionError("pyodbc is not available in this environment.")
    server, database, username, password = get_connection_string()
    if not all([server, database, username, password]):
        raise ConnectionError("Missing DB connection parameters.")
    driver = "ODBC Driver 18 for SQL Server"
    conn_str = (
        f"DRIVER={{{driver}}};SERVER=tcp:{server},1433;DATABASE={database};UID={username};PWD={password};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;Login Timeout=60;"
    )
    return pyodbc.connect(conn_str, autocommit=False, timeout=60)


def execute_non_query(query: str, params: Optional[tuple] = None) -> Tuple[bool, Optional[str]]:
    if MOCK_DATA:
        return True, None
    try:
        conn = get_db_connection()
    except Exception as e:
        return False, f"DB connect error: {e}"
    try:
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        return False, f"Execution error: {e}\n{traceback.format_exc()}"


def insert_and_get_id(insert_sql: str, params: tuple = None) -> Tuple[Optional[int], Optional[str]]:
    if MOCK_DATA:
        return int(datetime.utcnow().timestamp()), None
    try:
        conn = get_db_connection()
    except Exception as e:
        return None, f"DB connect error: {e}"
    try:
        cur = conn.cursor()
        if params:
            cur.execute(insert_sql, params)
        else:
            cur.execute(insert_sql)
        new_id = None
        try:
            row = cur.fetchone()
            if row and len(row) > 0 and row[0] is not None:
                new_id = int(row[0])
        except Exception:
            new_id = None
        conn.commit()
        cur.close()
        conn.close()
        return new_id, None
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass
        return None, f"Execution error: {e}\n{traceback.format_exc()}"

# UI: Public ticket form
st.title("Submit a Helpdesk Ticket")
st.write("Use this form to submit a request to VDH Service Center. Required fields are marked with *.")

with st.form("public_ticket_form"):
    name = st.text_input("Name *")
    email = st.text_input("Email *")
    location = st.selectbox("VDH Location *", ["Petersburg", "Hopewell", "Dinwiddie", "Surry", "Greensville/Emporia", "Prince George", "Sussex"])
    subject = st.text_input("Subject *")
    description = st.text_area("Description *", height=200)
    priority = st.selectbox("Priority *", ["Low", "Medium", "High", "Critical"])
    notify_me = st.checkbox("Email me a copy of this submission", value=False)
    submit = st.form_submit_button("Submit Ticket")

if submit:
    if not name or not email or not subject or not description:
        st.error("Please complete all required fields.")
    else:
        insert_sql = """
            INSERT INTO dbo.Tickets (name, email, location, short_description, description, status, priority, created_at)
            VALUES (?, ?, ?, ?, ?, 'New', ?, GETDATE());
            SELECT CAST(SCOPE_IDENTITY() AS INT) AS new_id;
        """
        new_id, err = insert_and_get_id(insert_sql, (name, email, location, subject, description, priority))
        if err:
            st.error(f"Failed to submit ticket: {err}")
        else:
            st.success("Thank you — your ticket has been submitted.")
            st.info(f"Ticket ID: {new_id}")
            # optional email send if SMTP enabled (kept minimal)

# Footer
st.markdown("---")
st.markdown("If you are an internal user with additional access, please use the internal VDH Service Center dashboard.")
