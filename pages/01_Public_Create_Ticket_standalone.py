# Standalone public "Create Helpdesk Ticket" page.
#
# Place this file at: pages/01_Public_Create_Ticket_standalone.py (on main)
#
# - Renders a simple public-looking ticket submission form.
# - Tries to insert into the DB (pyodbc + st.secrets / env vars). If DB fails, falls back to writing a CSV
#   at public_submissions/helpdesk_tickets.csv for reliable collection.
# - Suitable for committing directly to main; no other files or branches required.
#
import os
import csv
from pathlib import Path
from datetime import datetime
import traceback
import logging

import streamlit as st

# Try to import pyodbc; if not available we'll use CSV fallback
try:
    import pyodbc  # type: ignore
    HAS_PYODBC = True
except Exception:
    HAS_PYODBC = False

# Basic page config
st.set_page_config(page_title="Public - Submit Helpdesk Ticket", page_icon="🎫", layout="centered")
st.title("Public Helpdesk Ticket Submission")
st.write("Use this form to submit a helpdesk ticket. Fields marked with * are required.")

logger = logging.getLogger("public_submit_page")

# ---------------------------
# Helpers: DB connection + CSV fallback
# ---------------------------

def get_db_credentials():
    """
    Obtain DB connection details from st.secrets (preferred) or environment variables.
    Expected keys in st.secrets['database']: server, database, username, password
    """
    server = database = username = password = None
    try:
        cfg = st.secrets.get("database", {})
        server = cfg.get("server") or os.getenv("DB_SERVER")
        database = cfg.get("database") or os.getenv("DB_DATABASE")
        username = cfg.get("username") or os.getenv("DB_USERNAME")
        password = cfg.get("password") or os.getenv("DB_PASSWORD")
    except Exception:
        server = os.getenv("DB_SERVER")
        database = os.getenv("DB_DATABASE")
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
    return server, database, username, password

def get_db_connection():
    """
    Return a pyodbc.Connection or raise an Exception if connection cannot be made.
    Caller should handle the exception and fall back to CSV.
    """
    if not HAS_PYODBC:
        raise RuntimeError("pyodbc not installed in this environment")

    server, database, username, password = get_db_credentials()
    if not all([server, database, username, password]):
        raise RuntimeError("Missing DB credentials. Provide st.secrets['database'] or set env vars DB_SERVER/DB_DATABASE/DB_USERNAME/DB_PASSWORD")

    # Common driver; adjust if your environment differs
    driver = os.getenv("DB_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        f"UID={username};PWD={password};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str, autocommit=False, timeout=30)

def insert_ticket_db(name, email, phone, location, subject, priority, description):
    """
    Insert ticket into dbo.Tickets and return the new ticket id (int).
    The SQL expects a table with fields similar to the main app.
    """
    insert_sql = """
    INSERT INTO dbo.Tickets
      (name, email, phone_number, location, short_description, description, status, priority, created_at)
    VALUES (?, ?, ?, ?, ?, ?, 'New', ?, GETDATE());
    SELECT CAST(SCOPE_IDENTITY() AS INT) AS new_id;
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(insert_sql, (name, email, phone or None, location or None, subject, description, priority))
        row = cur.fetchone()
        new_id = None
        if row and row[0] is not None:
            new_id = int(row[0])
        conn.commit()
        cur.close()
        conn.close()
        return new_id
    except Exception as e:
        try:
            if conn:
                conn.rollback()
                conn.close()
        except Exception:
            pass
        raise

# CSV fallback storage
def ensure_submissions_dir():
    d = Path("public_submissions")
    d.mkdir(parents=True, exist_ok=True)
    return d

def append_submission_csv(row: dict, form_key: str = "helpdesk_tickets"):
    d = ensure_submissions_dir()
    filename = d / f"{form_key}.csv"
    file_exists = filename.exists()
    fieldnames = list(row.keys())
    with open(filename, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# ---------------------------
# Public form UI
# ---------------------------

with st.form("public_ticket_form"):
    col1, col2 = st.columns(2)
    with col1:
        full_name = st.text_input("Full name *", "")
        email = st.text_input("Email *", "")
        phone = st.text_input("Phone", "")
        location = st.selectbox("Preferred location", ["Petersburg", "Hopewell", "Dinwiddie", "Surry", "Greensville/Emporia", "Prince George", "Sussex", "Other"])
    with col2:
        subject = st.text_input("Subject *", "")
        priority = st.selectbox("Priority *", ["Low", "Medium", "High", "Critical"], index=1)
        description = st.text_area("Description *", height=200)

    attachments = st.file_uploader("Attachments (optional)", accept_multiple_files=True)
    submit_btn = st.form_submit_button("Submit Ticket")

# Handle submit
if submit_btn:
    if not full_name.strip() or not email.strip() or not subject.strip() or not description.strip():
        st.error("Please fill in all required fields: Full name, Email, Subject, Description.")
    else:
        now_iso = datetime.utcnow().isoformat() + "Z"
        fallback_id = datetime.utcnow().strftime("PUBL-%Y%m%d%H%M%S")
        attachment_names = ";".join([f.name for f in attachments]) if attachments else ""

        row = {
            "submission_id": fallback_id,
            "timestamp_utc": now_iso,
            "name": full_name,
            "email": email,
            "phone": phone or "",
            "location": location or "",
            "subject": subject,
            "priority": priority,
            "description": description,
            "attachments": attachment_names,
            "saved_to": "csv_fallback",
            "error": ""
        }

        # Try DB insert first
        db_ok = False
        new_ticket_id = None
        db_error_text = ""
        if HAS_PYODBC:
            try:
                new_ticket_id = insert_ticket_db(full_name, email, phone, location, subject, priority, description)
                db_ok = True
            except Exception as db_exc:
                db_error_text = f"{type(db_exc).__name__}: {str(db_exc)}"
                st.warning("Database insert failed — falling back to local CSV storage.")
                logger.exception("DB insert failed for public submission: %s", db_error_text)

        if db_ok and new_ticket_id:
            st.success(f"Thank you — your ticket has been submitted. Ticket ID: {new_ticket_id}")
            row["saved_to"] = "database"
            row["error"] = ""
            try:
                append_submission_csv(row)
            except Exception:
                pass
            if attachments:
                adir = ensure_submissions_dir() / str(new_ticket_id)
                adir.mkdir(parents=True, exist_ok=True)
                for f in attachments:
                    try:
                        contents = f.read()
                        with open(adir / f.name, "wb") as fh:
                            fh.write(contents)
                    except Exception:
                        pass
        else:
            row["saved_to"] = "csv_fallback"
            row["error"] = db_error_text
            try:
                append_submission_csv(row)
                if attachments:
                    adir = ensure_submissions_dir() / row["submission_id"]
                    adir.mkdir(parents=True, exist_ok=True)
                    for f in attachments:
                        try:
                            contents = f.read()
                            with open(adir / f.name, "wb") as fh:
                                fh.write(contents)
                        except Exception:
                            pass
                st.success(f"Thank you — your ticket has been received (temporary ID: {row['submission_id']}). We will import this into the database when available.")
                if db_error_text:
                    st.info("Reason: " + db_error_text)
            except Exception as csv_exc:
                st.error("Failed to save your submission. Please try again later or contact support.")
                logger.exception("Failed to save public submission to CSV: %s", csv_exc)

# ---------------------------
# Admin / Debug area (local only)
# ---------------------------
st.markdown("---")
st.caption("Admin / Debug (local testing only)")

if st.checkbox("Show recent fallback CSV submissions (debug)"):
    csv_file = Path("public_submissions/helpdesk_tickets.csv")
    if csv_file.exists():
        try:
            import pandas as pd  # local import for fallback debug only
            df = pd.read_csv(csv_file)
            st.write(f"Last {min(20, len(df))} submissions")
            st.dataframe(df.tail(20).iloc[:, :10])
        except Exception:
            rows = []
            with open(csv_file, "r", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                for r in list(reader)[-20:]:
                    rows.append(r)
            st.write(rows)

# End of file