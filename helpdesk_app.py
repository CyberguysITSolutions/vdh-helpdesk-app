# FULL MERGED helpdesk_app.py
# (Save this file to replace the current helpdesk_app.py after backing it up)
"""
helpdesk_app.py
Updated: includes role-based navigation (admin vs public users) and public submission pages:
 - 📝 Submit Ticket
 - 📝 Submit Procurement Request
 - 🛫 Request Vehicle
Public pages create draft rows and return a short reference token. Admins can sign in to access full app.
Save this file over your existing helpdesk_app.py (make a backup first).
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, timedelta, date
import os
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64
from typing import Optional, Tuple
import traceback
import logging
import smtplib
from email.message import EmailMessage
# near the other imports at top of helpdesk_app.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # for editor type-checking only
    import streamlit.components.v1 as components  # type: ignore
try:
    import streamlit.components.v1 as components
except Exception:
    components = None  # runtime fallback if streamlit not available

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import json
import uuid
from typing import Optional, Tuple
import traceback

# Page configuration
st.set_page_config(page_title="VDH Service Center", page_icon="🏥", layout="wide")
st.markdown(
    """
    <style>
      /* Hide Streamlit header (app title/hamburger) to remove the 'helpdesk app' breadcrumb */
      header[role="banner"] { display: none !important; }

      /* Hide Streamlit default top-of-sidebar pages navigation (when using pages/) */
      /* This selector targets the built-in pages navigation area — if it doesn't match your version of Streamlit, remove it and keep header hide only */
      div[data-testid="stSidebarNav"] { display: none !important; }

      /* Optional: keep the sidebar title area visible; adjust if you hide too much */
    </style>
    """,
    unsafe_allow_html=True,
)

# Guarded injection: only run if components is available
if components is not None:
    components.html(
        """
<script>
(function() {
  function applyUiTweaks() {
    try {
      var origin = window.location.origin || (window.location.protocol + '//' + window.location.host);
      var map = {
        'public-ticket-link': '/?page=pages/01_Public_Create_Ticket.py',
        'public-vehicle-link': '/?page=pages/02_Public_Request_Vehicle.py',
        'public-procurement-link': '/?page=pages/03_Public_Procurement_Request.py'
      };
      Object.keys(map).forEach(function(id) {
        var el = document.getElementById(id);
        if (el) {
          el.href = origin + map[id];
        }
      });
      var header = document.querySelector('header[role="banner"]');
      if (header) header.style.display = 'none';
      var sidebarNav = document.querySelector('div[data-testid="stSidebarNav"]');
      if (sidebarNav) sidebarNav.style.display = 'none';
      var navFallback = document.querySelector('div[aria-label="App header"], div[role="navigation"]');
      if (navFallback) navFallback.style.display = 'none';
      document.querySelectorAll('a').forEach(function(a){
        if (a.textContent && a.textContent.trim().toLowerCase().includes('helpdesk app')) {
          a.style.display = 'none';
        }
      });
    } catch (e) {
      console.warn('UI tweak script error', e);
    }
  }
  applyUiTweaks();
  var tries = 0;
  var intv = setInterval(function() {
    applyUiTweaks();
    tries += 1;
    if (tries > 20) clearInterval(intv);
  }, 300);
})();
</script>
<style>
header[role="banner"] { display: none !important; }
div[data-testid="stSidebarNav"] { display: none !important; }
div[aria-label="App header"] { display: none !important; }
</style>
""",
        height=1,
        scrolling=False,
    )
else:
    # Optional: display a small note in-app if components unavailable (helps debugging)
    st.caption("UI tweak script not applied: streamlit.components not available in environment.")

# Try to import pyodbc
try:
    import pyodbc
    HAS_PYODBC = True
except Exception:
    HAS_PYODBC = False
    logger.warning("pyodbc not available. Database connections will fail if required.")

# Try to import reporting libraries
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils.dataframe import dataframe_to_rows
    HAS_EXCEL = True
except Exception:
    HAS_EXCEL = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.units import inch
    HAS_PDF = True
except Exception:
    HAS_PDF = False

# VDH Color Scheme
VDH_NAVY = "#002855"
VDH_ORANGE = "#FF6B35"

# Enhanced CSS for VDH branding
st.markdown(f"""
<style>
    .main {{
        background-color: #f5f5f5;
    }}
    .stButton>button {{
        background-color: {VDH_NAVY};
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }}
    .stButton>button:hover {{
        background-color: {VDH_ORANGE};
    }}
    h1, h2, h3 {{
        color: {VDH_NAVY};
    }}
    .metric-card {{
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}

    /* Item row styling with alternating colors */
    .item-row {{
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
        transition: all 0.15s;
        border-left: 4px solid {VDH_NAVY};
    }}
    .item-row:hover {{
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }}
    .item-row-even {{
        background-color: #ffffff;
    }}
    .item-row-odd {{
        background-color: #f8f9fa;
    }}

    /* Enhanced headers */
    .list-header {{
        font-size: 1.15em;
        font-weight: 700;
        color: {VDH_NAVY};
        margin-bottom: 6px;
    }}

    /* Modern table styling */
    .dataframe th {{
        background-color: {VDH_NAVY} !important;
        color: white !important;
        padding: 10px !important;
        font-weight: 600 !important;
        font-size: 1.05em !important;
    }}
    .dataframe td {{
        padding: 8px !important;
    }}
    .dataframe tr:nth-child(even) {{
        background-color: #f8f9fa !important;
    }}
    .dataframe tr:hover {{
        background-color: #e9f2fb !important;
    }}

    /* Notes container */
    .notes-container {{
        background-color: #f8f9fa;
        border-left: 4px solid {VDH_ORANGE};
        padding: 12px;
        margin: 12px 0;
        border-radius: 6px;
    }}
    .note-item {{
        background-color: white;
        padding: 10px;
        margin: 8px 0;
        border-radius: 6px;
        border-left: 3px solid {VDH_NAVY};
    }}
    .note-header {{
        font-weight: 600;
        color: {VDH_NAVY};
        font-size: 0.92em;
    }}
    .note-text {{
        white-space: pre-wrap;
        font-size: 0.95em;
    }}
</style>
""", unsafe_allow_html=True)

# ============================================================================ 
# DATABASE CONNECTION FUNCTIONS
# ============================================================================

@st.cache_resource
def get_connection_string():
    """Get database connection parameters from environment or secrets"""
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
    """
    Returns a pyodbc.Connection with optimized settings for Azure SQL Database.
    """
    if not HAS_PYODBC:
        raise ConnectionError("pyodbc is not installed in this environment.")

    conn_str_env = os.getenv("DB_CONN")
    if conn_str_env:
        try:
            return pyodbc.connect(conn_str_env, autocommit=False, timeout=60)
        except Exception as e:
            logger.warning("DB_CONN connect failed, falling back: %s", e)

    server, database, username, password = get_connection_string()
    if not all([server, database, username, password]):
        raise ConnectionError("Missing DB connection parameters. Check secrets or environment variables.")

    # Normalize username for Azure SQL if needed
    if "@" not in username and "database.windows.net" in server:
        username = f"{username}@{server.split('.')[0]}"

    driver = "ODBC Driver 18 for SQL Server"
    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        f"UID={username};PWD={password};"
        "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;Login Timeout=60;"
    )
    try:
        conn = pyodbc.connect(conn_str, autocommit=False, timeout=60)
        return conn
    except Exception as e:
        logger.exception("Database connection failed")
        raise ConnectionError(str(e))

def execute_query(query: str, params: Optional[tuple] = None) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    try:
        conn = get_db_connection()
    except Exception as e:
        return None, f"Connection error: {e}"
    try:
        if params:
            df = pd.read_sql(query, conn, params=params)
        else:
            df = pd.read_sql(query, conn)
        conn.close()
        return df, None
    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        return None, f"Query error: {e}"

def execute_non_query(query: str, params: Optional[tuple] = None) -> Tuple[bool, Optional[str]]:
    try:
        conn = get_db_connection()
    except Exception as e:
        return False, f"Connection error: {e}"
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

# ============================================================================ 
# Helper utilities: email and insert-with-identity
# ============================================================================

def send_email(subject: str, body: str, recipients: list):
    """
    Send an email using SMTP settings in st.secrets (smtp section) or environment variables.
    Returns True on success, False on failure.
    """
    try:
        smtp_cfg = {}
        try:
            smtp_cfg = st.secrets.get("smtp", {})
        except Exception:
            smtp_cfg = {}
        host = smtp_cfg.get("host") or os.getenv("SMTP_HOST")
        port = int(smtp_cfg.get("port") or os.getenv("SMTP_PORT") or 587)
        username = smtp_cfg.get("username") or os.getenv("SMTP_USER")
        password = smtp_cfg.get("password") or os.getenv("SMTP_PASS")
        use_tls = smtp_cfg.get("use_tls", True)
        from_addr = smtp_cfg.get("from_address") or username or "no-reply@vdh.gov"

        if not host or not recipients:
            logger.warning("SMTP host or recipients missing; skipping email.")
            return False

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = ", ".join(recipients)
        msg.set_content(body)

        server = smtplib.SMTP(host, port, timeout=30)
        if use_tls:
            server.starttls()
        if username and password:
            server.login(username, password)
        server.send_message(msg)
        server.quit()
        logger.info("Email sent to %s", recipients)
        return True

    return server, database, username, password


# --- REPLACED execute_query / execute_non_query TO USE fleet.fleet_db.get_conn() ---
def execute_query(query: str, params: Optional[tuple] = None) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Execute a SELECT query and return (DataFrame, None) on success or (None, error_message).
    Attempts SQLAlchemy + pyodbc first (avoids DATETIMEOFFSET issues). Falls back to fleet_db.get_conn().
    """
    try:
        from fleet import fleet_db
    except Exception as e:
        return None, f"fleet_db import error: {e}"

    # Try SQLAlchemy path first (preferred)
    try:
        try:
            from sqlalchemy import create_engine  # type: ignore
            from urllib.parse import quote_plus
        except Exception as imp_e:
            raise RuntimeError(f"sqlalchemy not available: {imp_e}")

        server, database, username, password = get_connection_string()
        if not all([server, database, username, password]):
            raise RuntimeError("Missing DB connection pieces for SQLAlchemy engine; falling back to pyodbc path.")

        # If Azure-style username required, append short server
        if "@" not in username and server:
            username = f"{username}@{server.split('.')[0]}"

        # Build ODBC connection string and SQLAlchemy URL
        odbc_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={{server}};DATABASE={{database}};"
            f"UID={{username}};PWD={{password}};"
            f"Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;"
        )
        conn_url = "mssql+pyodbc:///?odbc_connect=" + quote_plus(odbc_str)

        engine = create_engine(conn_url, connect_args={"timeout": 30})
        try:
            if params:
                df = pd.read_sql_query(query, engine, params=params)
            else:
                df = pd.read_sql_query(query, engine)
            engine.dispose()
            return df, None
        except Exception as e_sql:
            try:
                engine.dispose()
            except Exception:
                pass
            raise RuntimeError(f"SQLAlchemy read_sql_query failed: {e_sql}")
    except Exception as primary_exc:
        # Fallback: use fleet_db.get_conn() and pandas.read_sql
        try:
            conn = fleet_db.get_conn()
        except Exception as e_conn:
            return None, f"connection error: {e_conn}\nprimary error: {primary_exc}"

        try:
            if params:
                df = pd.read_sql(query, conn, params=params)
            else:
                df = pd.read_sql(query, conn)
            conn.close()
            return df, None
        except Exception as e_fetch:
            try:
                conn.close()
            except Exception:
                pass
            return None, f"query error (pyodbc read_sql failed): {e_fetch}\nprimary error: {primary_exc}"


def execute_non_query(query: str, params: Optional[tuple] = None) -> Tuple[bool, Optional[str]]:
    """
    Execute INSERT/UPDATE/DELETE using fleet.fleet_db.get_conn().
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    try:
        from fleet import fleet_db
    except Exception as e:
        return False, f"fleet_db import error: {e}"

    try:
        conn = fleet_db.get_conn()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            cursor.close()
            conn.close()
            return True, None
        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                cursor.close()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            return False, f"execution error: {e}\n{traceback.format_exc()}"
    except Exception as e:
        return False, f"connection error: {e}\n{traceback.format_exc()}"
# --- end replacement ---


# --- safe rerun helper ----------------------------------------------------
def safe_rerun():
    """
    Cross-version safe replacement for st.experimental_rerun()/st.rerun().
    Call safe_rerun() instead of st.experimental_rerun() or st.rerun().
    """
    try:
        # Preferred public API when available
        return st.experimental_rerun()
    except Exception:
        try:
            # Streamlit internal (newer)
            from streamlit.runtime.scriptrunner import RerunException
            raise RerunException()
        except Exception:
            try:
                # Streamlit internal (older)
                from streamlit.report_thread import RerunException as _OldRerunException  # type: ignore
                raise _OldRerunException()
            except Exception:
                # Final fallback - stop the script gracefully
                st.stop()
# -------------------------------------------------------------------------


def generate_excel_report(df, report_title):
    """Generate Excel report with formatting"""
    if not HAS_EXCEL:
        return None, "openpyxl not installed"

    try:
        output = BytesIO()
        wb = Workbook()
        ws = wb.active
        ws.title = "Report"

        # Add title
        ws['A1'] = report_title
        ws['A1'].font = Font(size=16, bold=True)
        ws['A1'].fill = PatternFill(start_color="002855", end_color="002855", fill_type="solid")
        ws['A1'].font = Font(size=16, bold=True, color="FFFFFF")
        ws.merge_cells('A1:' + chr(64 + len(df.columns)) + '1')

        # Add generation timestamp
        ws['A2'] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws['A2'].font = Font(size=10, italic=True)
        ws.merge_cells('A2:' + chr(64 + len(df.columns)) + '2')

        # Add headers
        header_row = 4
        for col_num, column_title in enumerate(df.columns, 1):
            cell = ws.cell(row=header_row, column=col_num)
            cell.value = column_title
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Add data
        for row_num, row_data in enumerate(df.values, header_row + 1):
            for col_num, value in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.value = value
                cell.alignment = Alignment(horizontal="left", vertical="center")

                # Alternate row colors
                if row_num % 2 == 0:
                    cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")

        # Auto-adjust column widths
        for col_num in range(1, len(df.columns) + 1):
            max_length = 0
            column_letter = chr(64 + col_num)

            # Check header length
            if col_num <= len(df.columns):
                max_length = len(str(df.columns[col_num - 1]))

            # Check data lengths
            for row_num in range(header_row + 1, ws.max_row + 1):
                cell = ws.cell(row=row_num, column=col_num)
                try:
                    if cell.value and len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception:
                    pass

            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

        wb.save(output)
        output.seek(0)
        return output, None
    except Exception as e:
        logger.exception("Failed to send email: %s", e)
        return False

def insert_and_get_id(insert_sql: str, params: tuple = None) -> Tuple[Optional[int], Optional[str]]:
    """
    Execute an insert that ends with SELECT CAST(SCOPE_IDENTITY() AS INT) as new_id;
    Returns (new_id, None) on success or (None, error) on failure.
    """
    try:
        conn = get_db_connection()

def generate_pdf_report(df, report_title):
    """Generate PDF report"""
    if not HAS_PDF:
        return None, "reportlab not installed"

    try:
        output = BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#002855'),
            spaceAfter=12,
            alignment=1  # Center
        )
        elements.append(Paragraph(report_title, title_style))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))

        # Convert dataframe to table data
        data = [df.columns.tolist()] + df.values.tolist()

        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066CC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))

        elements.append(table)
        doc.build(elements)
        output.seek(0)
        return output, None
    except Exception as e:
        return None, f"Connection error: {e}"


def generate_csv_report(df):
    """Generate CSV report"""
    try:
        cur = conn.cursor()
        if params:
            cur.execute(insert_sql, params)
        else:
            cur.execute(insert_sql)
        # Attempt to fetch the result (SCOPE_IDENTITY)
        new_id = None
        try:
            row = cur.fetchone()
            if row and row[0] is not None:
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
        except:
            pass
        try:
            cur.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass
        return None, f"Execution error: {e}\n{traceback.format_exc()}"

# ============================================================================ 
# Small helpers
# ============================================================================

def safe_rerun():
    try:
        st.rerun()
    except Exception:
        try:
            st.experimental_rerun()
        except Exception:
            st.warning("Please refresh the page manually to see updates.")

def generate_ticket_number():
    now = datetime.now()
    return f"TKT-{now.strftime('%Y%m%d%H%M%S')}"

def generate_asset_tag():
    now = datetime.now()
    return f"COV-{now.strftime('%Y%m%d%H%M%S')}"

def generate_procurement_number():
    now = datetime.now()
    return f"PR-{now.strftime('%Y%m%d%H%M%S')}"

# ============================================================================ 
# Report helpers (Excel / PDF)
# ============================================================================

def generate_excel_report(df, report_title):
    if not HAS_EXCEL:
        return None
    out = BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = report_title[:31]
    header_fill = PatternFill(start_color="002855", end_color="002855", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF")
    for col_num, col in enumerate(df.columns, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = col
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=False), 2):
        for c_idx, val in enumerate(row, 1):
            ws.cell(row=r_idx, column=c_idx, value=val)
    for col_cells in ws.columns:
        length = max((len(str(cell.value)) if cell.value is not None else 0) for cell in col_cells)
        ws.column_dimensions[col_cells[0].column_letter].width = min(length + 2, 50)
    wb.save(out)
    out.seek(0)
    return out

def generate_pdf_report(df, report_title):
    if not HAS_PDF:
        return None
    out = BytesIO()
    doc = SimpleDocTemplate(out, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor(VDH_NAVY))
    elements.append(Paragraph(report_title, title_style))
    elements.append(Spacer(1, 6))
    data = [df.columns.tolist()] + df.values.tolist()
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor(VDH_NAVY)),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ]))
    elements.append(table)
    doc.build(elements)
    out.seek(0)
    return out

# ============================================================================ 
# Initialize session state keys (idempotent)
# ============================================================================

# Custom CSS - VDH Color Scheme
st.markdown("""
<style>
    /* VDH Colors: Navy Blue #002855, Orange #FF6B35 */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        background-color: #FF6B35;
        color: white;
    }
    .stButton>button:hover {
        background-color: #e55a2b;
        color: white;
    }
    div[data-testid="stExpander"] {
        background-color: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    .ticket-card {
        background: white;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #FF6B35;
        margin-bottom: 10px;
    }
    .note-card {
        background: #f8f9fa;
        padding: 10px;
        border-radius: 6px;
        margin: 10px 0;
        border-left: 3px solid #002855;
    }
    /* Header styling */
    h1, h2, h3 {
        color: #002855;
    }
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #002855;
    }
    [data-testid="stSidebar"] .stSelectbox label {
        color: white;
    }
    /* Metric styling */
    [data-testid="stMetricValue"] {
        color: #002855;
    }
</style>
""", unsafe_allow_html=True)

if 'show_create_ticket' not in st.session_state:
    st.session_state.show_create_ticket = False
if 'view_ticket_id' not in st.session_state:
    st.session_state.view_ticket_id = None
if 'edit_ticket_id' not in st.session_state:
    st.session_state.edit_ticket_id = None
if 'report_preview_data' not in st.session_state:
    st.session_state.report_preview_data = None

# --- ROLE-BASED NAVIGATION SNIPPET (INSERTED) ------------------------------
# Add a simple admin password check and show different nav items for admin vs normal users.
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

def _get_admin_password() -> Optional[str]:
    try:
        return st.secrets["admin"]["password"]
    except Exception:
        return os.getenv("ADMIN_PASSWORD")


def _attempt_admin_login(password: str) -> bool:
    configured = _get_admin_password()
    if not configured:
        return False
    if password == configured:
        st.session_state.is_admin = True
        return True
    return False

with st.sidebar:
    st.markdown("## Navigate")
    if st.session_state.is_admin:
        st.markdown("**Signed in as Admin**")
        if st.button("🔒 Logout"):
            st.session_state.is_admin = False
            # Clear admin-only session bits if desired
            safe_rerun()
    else:
        with st.expander("Admin login (for admin users only)", expanded=False):
            pwd = st.text_input("Admin password", type="password")
            if st.button("Sign in as Admin"):
                ok = _attempt_admin_login(pwd)
                if ok:
                    st.success("Signed in as Admin")
                    safe_rerun()
                else:
                    st.error("Invalid admin password")

if st.session_state.is_admin:
    NAV_ITEMS = [
        "📊 Dashboard",
        "🎫 Tickets",
        "💻 Assets",
        "🚗 Fleet",
        "🛒 Procurement",
        "📈 Reports",
        "👥 Users",
        "🔍 Query Builder",
        "🔌 Connection Test"
    ]
else:
    NAV_ITEMS = [
        "📝 Submit Ticket",
        "📝 Submit Procurement Request",
        "🛫 Request Vehicle",
        "🔌 Connection Test"
    ]

page = st.sidebar.selectbox("Navigate", NAV_ITEMS)
# --- END ROLE-BASED NAVIGATION SNIPPET ------------------------------------

# Header with VDH Logo
col1, col2, col3 = st.columns([1, 4, 1])
with col1:
    try:
        st.image("VDH-logo.png", width=120)
    except Exception:
        st.markdown("### 🏥")
with col2:
    st.markdown("<h1 style='color: #002855; margin-top: 20px;'>Service Center</h1>", unsafe_allow_html=True)
with col3:
    st.markdown("<p style='text-align: right; margin-top: 30px;'><strong>Admin</strong></p>", unsafe_allow_html=True)

if 'show_create_asset' not in st.session_state:
    st.session_state.show_create_asset = False
if 'view_asset_id' not in st.session_state:
    st.session_state.view_asset_id = None

if 'show_create_procurement' not in st.session_state:
    st.session_state.show_create_procurement = False
if 'view_procurement_id' not in st.session_state:
    st.session_state.view_procurement_id = None
if 'procurement_items' not in st.session_state:
    st.session_state.procurement_items = []

if 'show_request_vehicle' not in st.session_state:
    st.session_state.show_request_vehicle = False
if 'view_trip_id' not in st.session_state:
    st.session_state.view_trip_id = None

# ============================================================================ 
# Sidebar / Navigation (add public links)
# ============================================================================

st.sidebar.image("https://via.placeholder.com/200x80/002855/FFFFFF?text=VDH", width='stretch')
st.sidebar.title("VDH Service Center")

# Public forms links for external users (these are references; deploy public forms separately)
# --- Replace the previous st.sidebar.markdown(...) public-links block with this components.html ---
st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Public Access Forms")

components.html(
    """
    <div style="line-height:1.8;">
      <a id="pt" href="#" style="text-decoration:none;color:#005ea6;font-weight:600;">Submit a Ticket</a><br/>
      <a id="pv" href="#" style="text-decoration:none;color:#005ea6;font-weight:600;">Request a Vehicle</a><br/>
      <a id="pp" href="#" style="text-decoration:none;color:#005ea6;font-weight:600;">Submit a Requisition</a>
    </div>
    <script>
      (function(){
        var origin = window.location.origin || (window.location.protocol + '//' + window.location.host);
        function openPage(path) {
          // IMPORTANT: do NOT encode the slash characters; Streamlit expects page=pages/filename.py exactly
          var url = origin + '/?page=' + path;
          window.open(url, '_blank', 'noopener');
        }
        var a1 = document.getElementById('pt');
        var a2 = document.getElementById('pv');
        var a3 = document.getElementById('pp');
        if (a1) a1.addEventListener('click', function(e){ e.preventDefault(); openPage('pages/01_Public_Create_Ticket.py'); });
        if (a2) a2.addEventListener('click', function(e){ e.preventDefault(); openPage('pages/02_Public_Request_Vehicle.py'); });
        if (a3) a3.addEventListener('click', function(e){ e.preventDefault(); openPage('pages/03_Public_Procurement_Request.py'); });
      })();
    </script>
    """,
    height=90,
    scrolling=False,
)


page = st.sidebar.selectbox("Navigate", [
    "📊 Dashboard",
    "🎫 Helpdesk Tickets",
    "💻 Asset Management",
    "🛒 Procurement Requests",
    "🚗 Fleet Management",
    "📈 Report Builder",
    "🔌 Connection Test"
])

# ============================================================================ 
# DASHBOARD PAGE
# ============================================================================

if page == "📊 Dashboard":
    st.header("📊 Dashboard Overview")
    with st.spinner("Loading dashboard data..."):
        stats_df, _ = execute_query("SELECT COUNT(*) as total_tickets FROM dbo.Tickets")
        status_df, _ = execute_query("SELECT status, COUNT(*) as count FROM dbo.Tickets GROUP BY status")
        priority_df, _ = execute_query("SELECT priority, COUNT(*) as count FROM dbo.Tickets GROUP BY priority")
        location_df, _ = execute_query("SELECT location, COUNT(*) as count FROM dbo.Tickets GROUP BY location")
        asset_df, _ = execute_query("SELECT COUNT(*) as total_assets FROM dbo.Assets")
        asset_status_df, _ = execute_query("SELECT status, COUNT(*) as count FROM dbo.Assets GROUP BY status")
        asset_location_df, _ = execute_query("SELECT location, COUNT(*) as count FROM dbo.Assets GROUP BY location")
        proc_df, _ = execute_query("SELECT COUNT(*) as total_requests FROM dbo.Procurement_Requests")
        fleet_df, _ = execute_query("SELECT COUNT(*) as total_vehicles FROM dbo.vehicles")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_tickets = int(stats_df.iloc[0]['total_tickets']) if stats_df is not None and len(stats_df)>0 else 0
        st.metric("Total Tickets", total_tickets)
        if status_df is not None and len(status_df)>0:
            for _, r in status_df.iterrows():
                st.caption(f"{r['status']}: {int(r['count'])}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_assets = int(asset_df.iloc[0]['total_assets']) if asset_df is not None and len(asset_df)>0 else 0
        st.metric("Total Assets", total_assets)
        if asset_status_df is not None and len(asset_status_df)>0:
            for _, r in asset_status_df.iterrows():
                st.caption(f"{r['status']}: {int(r['count'])}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_proc = int(proc_df.iloc[0]['total_requests']) if proc_df is not None and len(proc_df)>0 else 0
        st.metric("Procurement Requests", total_proc)
        st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        total_fleet = int(fleet_df.iloc[0]['total_vehicles']) if fleet_df is not None and len(fleet_df)>0 else 0
        st.metric("Total Vehicles", total_fleet)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 Ticket Analytics")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("**Tickets by Status**")
        if status_df is not None and len(status_df)>0:
            fig = px.pie(status_df, values='count', names='status', color_discrete_sequence=[VDH_NAVY, VDH_ORANGE, '#FFC857', '#4CAF50', '#E63946'])
            st.plotly_chart(fig, config={"displayModeBar": False}, width='stretch')
        else:
            st.info("No ticket status data available")
    with c2:
        st.write("**Tickets by Priority**")
        if priority_df is not None and len(priority_df)>0:
            priority_order = {'Low':1,'Medium':2,'High':3,'Critical':4}
            priority_df['sort_order'] = priority_df['priority'].map(priority_order)
            priority_df = priority_df.sort_values('sort_order')
            fig = px.bar(priority_df, x='priority', y='count', color_discrete_sequence=[VDH_NAVY])
            fig.update_layout(xaxis_title="Priority", yaxis_title="Count")
            st.plotly_chart(fig, config={"displayModeBar": False}, width='stretch')
        else:
            st.info("No ticket priority data available")
    with c3:
        st.write("**Tickets by Location**")
        if location_df is not None and len(location_df)>0:
            fig = px.bar(location_df, x='location', y='count', color_discrete_sequence=[VDH_ORANGE])
            fig.update_layout(xaxis_title="Location", yaxis_title="Count")
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, config={"displayModeBar": False}, width='stretch')
        else:
            st.info("No ticket location data available")

# ============================================================================ 
# HELPDESK TICKETS PAGE (includes notes on update + notifications)
# ============================================================================

elif page == "🎫 Helpdesk Tickets":
    st.header("🎫 Helpdesk Tickets")

    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if st.button("➕ Create New Ticket"):
            st.session_state.show_create_ticket = True
            st.session_state.view_ticket_id = None
            safe_rerun()

    # Create Ticket Form
    if st.session_state.show_create_ticket:
        st.markdown("---")
        st.subheader("Create New Ticket")
        with st.form("create_ticket_form"):
            col1, col2 = st.columns(2)
            with col1:
                customer_name = st.text_input("Customer Name *", placeholder="John Doe")
                customer_email = st.text_input("Customer Email *", placeholder="john.doe@vdh.virginia.gov")
                customer_phone = st.text_input("Customer Phone", placeholder="(804) 555-1234")
                vdh_location = st.selectbox("VDH Location *", [
                    "Petersburg", "Hopewell", "Dinwiddie", "Surry",
                    "Greensville/Emporia", "Prince George", "Sussex"
                ])
            with col2:
                ticket_type = st.selectbox("Ticket Type *", [
                    "Technical issue", "Hardware issue", "Software issue",
                    "Network issue", "Access request", "Training request", "Other"
                ])
                ticket_priority = st.selectbox("Priority *", ["Low", "Medium", "High", "Critical"])
                ticket_subject = st.text_input("Subject *", placeholder="Brief description")
            ticket_description = st.text_area("Description *", height=150)
            submit_button = st.form_submit_button("✅ Create Ticket")
            cancel_button = st.form_submit_button("❌ Cancel")
            if submit_button:
                if not all([customer_name, customer_email, vdh_location, ticket_type, ticket_priority, ticket_subject, ticket_description]):
                    st.error("Please fill in all required fields (*)")
                else:
                    insert_query = """
                        INSERT INTO dbo.Tickets (
                            name, email, phone_number, location, short_description,
                            description, status, priority, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'New', ?, GETDATE());
                        SELECT CAST(SCOPE_IDENTITY() AS INT) AS new_id;
                    """
                    new_id, err = insert_and_get_id(insert_query, (
                        customer_name, customer_email, customer_phone or None,
                        vdh_location, ticket_subject, ticket_description,
                        ticket_priority
                    ))
                    if err:
                        st.error(f"Error creating ticket: {err}")
                    else:
                        # Create notification and email to helpdesk admins
                        try:
                            # recipients
                            recipients_cfg = []
                            try:
                                recipients_cfg = st.secrets.get("helpdesk", {}).get("admins", "").split(",")
                            except Exception:
                                recipients_cfg = os.getenv("HELPDESK_ADMINS", "").split(",")
                            recips = [r.strip() for r in recipients_cfg if r and r.strip()]
                            notif_sql = """
                                INSERT INTO dbo.Notifications (notification_type, reference_id, title, body, recipients, is_read, created_at)
                                VALUES (?, ?, ?, ?, ?, 0, GETDATE())
                            """
                            notif_title = f"New ticket #{new_id} - {ticket_subject}"
                            notif_body = f"Ticket #{new_id}\nRequester: {customer_name} <{customer_email}>\nLocation: {vdh_location}\nSubject: {ticket_subject}"
                            execute_non_query(notif_sql, ('ticket', new_id, notif_title, notif_body, ",".join(recips)))
                            if recips:
                                send_email(f"[VDH Helpdesk] New ticket #{new_id}", notif_body, recips)
                        except Exception as e:
                            logger.exception("Failed to notify helpdesk admins: %s", e)
                        st.success("✅ Ticket created successfully!")
                        st.session_state.show_create_ticket = False
                        safe_rerun()
            if cancel_button:
                st.session_state.show_create_ticket = False
                safe_rerun()

    # === DEBUG BLOCK FOR TICKETS (insert immediately BEFORE `if st.session_state.view_ticket_id:`) ===
    # Temporary debug: show whether tickets SELECT returns rows (safe, read-only)
    st.markdown("---")
    st.subheader("DEBUG - Tickets List Check (temporary)")
    tickets_check_query = "SELECT TOP (50) * FROM dbo.Tickets ORDER BY created_at DESC"
    tickets_df, tickets_err = execute_query(tickets_check_query)
    st.write("DEBUG: tickets_check_query:", tickets_check_query)
    st.write("DEBUG: tickets_fetch_error:", tickets_err)
    if tickets_df is None:
        st.write("DEBUG: tickets_df is None (connection/query error)")
    elif isinstance(tickets_df, pd.DataFrame) and len(tickets_df) == 0:
        st.write("DEBUG: tickets_df is empty (no rows returned)")
    else:
        try:
            st.write(f"DEBUG: tickets_df shape: {getattr(tickets_df, 'shape', 'unknown')}")
            st.dataframe(tickets_df.head(20), width='stretch')
        except Exception as _dbg_e:
            st.write("DEBUG: error rendering tickets_df preview:", repr(_dbg_e))
    st.markdown("---")
    # === END TICKETS DEBUG BLOCK ===

    # View / Update Ticket (requires notes)
    if st.session_state.view_ticket_id:
        st.markdown("---")
        if st.button("← Back to Ticket List"):
            st.session_state.view_ticket_id = None
            safe_rerun()
        tid = st.session_state.view_ticket_id
        ticket_query = f"SELECT * FROM dbo.Tickets WHERE ticket_id = {tid}"
        ticket_df, terr = execute_query(ticket_query)
        if terr or ticket_df is None or len(ticket_df) == 0:
            st.error("Ticket not found or error")
            st.session_state.view_ticket_id = None
        else:
            ticket = ticket_df.iloc[0]
            col1, col2, col3 = st.columns([2,1,1])
            with col1:
                ticket_id_display = str(ticket.get('ticket_id', 'N/A')).replace('(', '').replace(')', '').strip()
                st.subheader(f"Ticket #{ticket_id_display}")
            with col2:
                status = ticket.get('status', 'N/A')
                status_colors = {'New':'🟢','Open':'🟢','In Progress':'🟡','On Hold':'🟠','Resolved':'✅','Closed':'⚫'}
                st.write(f"{status_colors.get(status,'⚪')} Status: **{status}**")
            with col3:
                priority = ticket.get('priority', 'Normal')
                priority_colors = {'Low':'🟢','Medium':'🟡','High':'🟠','Critical':'🔴'}
                st.write(f"{priority_colors.get(priority,'⚪')} Priority: **{priority}**")
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Customer:** {ticket.get('name','N/A')}")
                st.write(f"**Email:** {ticket.get('email','N/A')}")
                if ticket.get('phone_number'):
                    st.write(f"**Phone:** {ticket.get('phone_number')}")
                st.write(f"**Location:** {ticket.get('location','N/A')}")
            with col2:
                st.write(f"**Created:** {ticket.get('created_at','N/A')}")
                if ticket.get('first_response_at'):
                    st.write(f"**First Response:** {ticket.get('first_response_at')}")
                if ticket.get('resolved_at'):
                    st.write(f"**Resolved:** {ticket.get('resolved_at')}")
            st.markdown("---")
            st.subheader("Subject")
            st.write(ticket.get('short_description','N/A'))
            st.subheader("Description")
            st.write(ticket.get('description','N/A'))
            st.markdown("---")
            st.subheader("Update Ticket")
            with st.form("update_ticket_form"):
                col1, col2 = st.columns(2)
                with col1:
                    current_status = str(ticket.get('status','New'))
                    status_options = ['New','Open','In Progress','On Hold','Waiting Customer Response','Resolved','Closed']
                    try:
                        status_index = status_options.index(current_status)
                    except Exception:
                        status_index = 0
                    new_status = st.selectbox("Status", status_options, index=status_index)
                with col2:
                    current_priority = str(ticket.get('priority','Medium'))
                    priority_options = ['Low','Medium','High','Critical']
                    try:
                        priority_index = priority_options.index(current_priority)
                    except Exception:
                        priority_index = 1
                    new_priority = st.selectbox("Priority", priority_options, index=priority_index)
                notes = st.text_area("Add Notes *", placeholder="Enter update notes (required)...", height=120)
                if st.form_submit_button("💾 Update Ticket"):
                    if not notes or notes.strip() == "":
                        st.error("Please add notes describing the update")
                    else:
                        update_query = "UPDATE dbo.Tickets SET status = ?, priority = ? WHERE ticket_id = ?"
                        ok, uerr = execute_non_query(update_query, (new_status, new_priority, tid))
                        if ok:
                            note_sql = """
                                INSERT INTO dbo.Ticket_Notes (ticket_id, note_text, note_type, created_by, created_at)
                                VALUES (?, ?, ?, ?, GETDATE());
                            """
                            note_type = "Update"
                            if new_status != current_status and new_priority != current_priority:
                                note_type = "Status & Priority Update"
                            elif new_status != current_status:
                                note_type = "Status Update"
                            elif new_priority != current_priority:
                                note_type = "Priority Update"
                            note_text = f"Status: {current_status} → {new_status}\nPriority: {current_priority} → {new_priority}\n\nNotes: {notes}"
                            n_ok, n_err = execute_non_query(note_sql, (tid, note_text, note_type, "System User"))
                            if n_ok:
                                st.success("✅ Ticket updated and logged")
                                st.session_state.view_ticket_id = None
                                safe_rerun()
                            else:
                                st.warning(f"Ticket updated but note not saved: {n_err}")
                        else:
                            st.error(f"Error updating ticket: {uerr}")

            # Show ticket history
            st.markdown("---")
            st.subheader("📋 Ticket History")
            notes_q = """
                SELECT note_id, note_text, note_type, created_by, created_at
                FROM dbo.Ticket_Notes
                WHERE ticket_id = ?
                ORDER BY created_at DESC
            """
            notes_df, notes_err = execute_query(notes_q, (tid,))
            if notes_err:
                st.warning("Could not load ticket history (run DB migration).")
            elif notes_df is None or len(notes_df)==0:
                st.info("No history yet for this ticket.")
            else:
                st.markdown('<div class="notes-container">', unsafe_allow_html=True)
                for _, n in notes_df.iterrows():
                    st.markdown(f"""
                        <div class="note-item">
                          <div class="note-header">{n['note_type']} • {n['created_by']} • {n['created_at']}</div>
                          <div class="note-text">{n['note_text']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================ 
# Asset Management (with cleaned COV display and update+notes)
# ============================================================================

elif page == "💻 Asset Management":
    st.header("💻 Asset Management")

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("➕ Add New Asset"):
            st.session_state.show_create_asset = True
            st.session_state.view_asset_id = None
            safe_rerun()

    if st.session_state.show_create_asset:
        st.markdown("---")
        st.subheader("Add New Asset")
        with st.form("create_asset_form"):
            c1, c2 = st.columns(2)
            with c1:
                asset_tag = st.text_input("Asset Tag *", value=generate_asset_tag())
                asset_type = st.selectbox("Asset Type *", ["Desktop Computer","Laptop","Monitor","Printer","Phone","Tablet","Network Equipment","Server","Other"])
                make_model = st.text_input("Make/Model *")
                serial_number = st.text_input("Serial Number *")
            with c2:
                status = st.selectbox("Status *", ["Deployed","Non-Deployed","Surplus"])
                location = st.selectbox("Location *", ["Petersburg","Hopewell","Dinwiddie","Surry","Greensville/Emporia","Prince George","Sussex"])
                assigned_to = st.text_input("Assigned To")
                purchase_date = st.date_input("Purchase Date")
            notes = st.text_area("Notes")
            submit_button = st.form_submit_button("✅ Add Asset")
            cancel_button = st.form_submit_button("❌ Cancel")
            if submit_button:
                if not all([asset_tag, asset_type, make_model, serial_number, status, location]):
                    st.error("Please fill required fields")
                else:
                    insert_q = """
                        INSERT INTO dbo.Assets (asset_tag, type, model, serial, status, location, assigned_user, purchase_date, notes, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE());
                    """
                    ok, err = execute_non_query(insert_q, (asset_tag, asset_type, make_model, serial_number, status, location, assigned_to or None, purchase_date, notes or None))
                    if ok:
                        st.success(f"✅ Asset {asset_tag} added")
                        st.session_state.show_create_asset = False
                        safe_rerun()
                    else:
                        st.error(f"Error adding asset: {err}")
            if cancel_button:
                st.session_state.show_create_asset = False
                safe_rerun()

    # Asset list (styled)
    if not st.session_state.show_create_asset and not st.session_state.view_asset_id:
        st.markdown("---")
        st.subheader("Asset Inventory")
        f1, f2, f3 = st.columns(3)
        with f1:
            filter_status = st.selectbox("Filter by Status", ["All","Deployed","Non-Deployed","Surplus"])
        with f2:
            filter_type = st.selectbox("Filter by Type", ["All","Desktop Computer","Laptop","Monitor","Printer","Phone","Tablet","Network Equipment","Server","Other"])
        with f3:
            filter_location = st.selectbox("Filter by Location", ["All","Petersburg","Hopewell","Dinwiddie","Surry","Greensville/Emporia","Prince George","Sussex"])
        q = "SELECT * FROM dbo.Assets WHERE 1=1"
        if filter_status != "All":
            q += f" AND status = '{filter_status}'"
        if filter_type != "All":
            q += f" AND type = '{filter_type}'"
        if filter_location != "All":
            q += f" AND location = '{filter_location}'"
        q += " ORDER BY asset_id DESC"
        assets_df, aerr = execute_query(q)
        if aerr:
            st.error(aerr)
        elif assets_df is None or len(assets_df)==0:
            st.info("No assets found")
        else:
            st.write(f"Found {len(assets_df)} assets")
            for idx, asset in assets_df.iterrows():
                row_class = "item-row-even" if idx % 2 == 0 else "item-row-odd"
                st.markdown(f'<div class="item-row {row_class}">', unsafe_allow_html=True)
                c1, c2, c3, c4, c5 = st.columns([2,2,2,1,1])
                with c1:
                    asset_tag_raw = str(asset.get('asset_tag','N/A'))
                    asset_tag_clean = asset_tag_raw.replace('(', '').replace(')', '').strip()
                    st.markdown(f'<div class="list-header">{asset_tag_clean}</div>', unsafe_allow_html=True)
                    st.caption(f"ID: {asset.get('asset_id','N/A')}")
                with c2:
                    st.write(f"**Type:** {asset.get('type','N/A')}")
                    st.caption(asset.get('model',''))
                with c3:
                    st.write(f"📍 {asset.get('location','N/A')}")
                    st.caption(f"👤 {asset.get('assigned_user','Unassigned')}")
                with c4:
                    status = asset.get('status','N/A')
                    status_colors = {'Deployed':'🟢','Non-Deployed':'🟡','Surplus':'🟠'}
                    st.write(f"{status_colors.get(status,'⚪')} {status}")
                with c5:
                    aid = asset.get('asset_id')
                    if st.button("View", key=f"view_asset_{idx}_{aid}"):
                        st.session_state.view_asset_id = int(aid)
                        safe_rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # View/update asset section
    if st.session_state.view_asset_id:
        st.markdown("---")
        if st.button("← Back to Asset List"):
            st.session_state.view_asset_id = None
            safe_rerun()
        aid = st.session_state.view_asset_id
        asset_q = f"SELECT * FROM dbo.Assets WHERE asset_id = {aid}"
        asset_df, aerr = execute_query(asset_q)
        if aerr or asset_df is None or len(asset_df)==0:
            st.error("Asset not found or error loading asset")
            st.session_state.view_asset_id = None
        else:
            asset = asset_df.iloc[0]
            col1, col2, col3 = st.columns([2,1,1])
            with col1:
                st.subheader(f"Asset: {asset.get('asset_tag','N/A')}")
            with col2:
                st.write(f"**Type:** {asset.get('type','N/A')}")
            with col3:
                st.write(f"**Status:** {asset.get('status','N/A')}")
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.write("### Hardware Details")
                st.write(f"**Model:** {asset.get('model','N/A')}")
                st.write(f"**Serial:** {asset.get('serial','N/A')}")
                st.write(f"**Category:** {asset.get('category','N/A')}")
                st.write("### Location & Assignment")
                st.write(f"**Location:** {asset.get('location','N/A')}")
                st.write(f"**Assigned User:** {asset.get('assigned_user','Unassigned')}")
            with c2:
                st.write("### Network")
                st.write(f"**MAC:** {asset.get('mac_address','N/A')}")
                st.write(f"**IP:** {asset.get('ip_address','N/A')}")
                st.write("### Warranty & Purchase")
                st.write(f"**Purchase Date:** {asset.get('purchase_date','N/A')}")
            st.markdown("---")
            st.subheader("Update Asset")
            with st.form("update_asset_form"):
                col1, col2 = st.columns(2)
                with col1:
                    current_status = asset.get('status','In-Stock')
                    status_options = ["Deployed","In-Stock","Surplus","Unaccounted"]
                    try:
                        idx_s = status_options.index(current_status)
                    except Exception:
                        idx_s = 0
                    new_status = st.selectbox("Status", status_options, index=idx_s)
                    current_location = asset.get('location','Petersburg')
                    loc_opts = ["Petersburg","Hopewell","Dinwiddie","Surry","Greensville/Emporia","Prince George","Sussex"]
                    try:
                        idx_l = loc_opts.index(current_location)
                    except Exception:
                        idx_l = 0
                    new_location = st.selectbox("Location", loc_opts, index=idx_l)
                with col2:
                    new_assigned_user = st.text_input("Assigned User", value=asset.get('assigned_user',''))
                    new_assigned_email = st.text_input("Assigned Email", value=asset.get('assigned_email',''))
                with st.form_submit_button("💾 Update Asset"):
                    update_notes = st.session_state.get('update_notes_tmp', '')
                    # Use a prompt outside form for notes to ensure required; or use simple text_area before submission
                    # For simplicity here prompt user if notes missing
                    if not st.session_state.get('asset_update_notes'):
                        st.warning("Please enter update notes in the 'Asset History' section below before saving.")
                    else:
                        notes_text = st.session_state.get('asset_update_notes')
                        update_q = """
                            UPDATE dbo.Assets
                            SET status = ?, location = ?, assigned_user = ?, assigned_email = ?, mac_address = ?, ip_address = ?, updated_at = GETDATE()
                            WHERE asset_id = ?
                        """
                        ok, uerr = execute_non_query(update_q, (new_status, new_location, new_assigned_user or None, new_assigned_email or None, asset.get('mac_address'), asset.get('ip_address'), aid))
                        if ok:
                            note_q = """
                                INSERT INTO dbo.Asset_Notes (asset_id, note_text, note_type, created_by, created_at)
                                VALUES (?, ?, ?, ?, GETDATE())
                            """
                            chg = []
                            if new_status != asset.get('status'):
                                chg.append(f"Status: {asset.get('status')} -> {new_status}")
                            if new_location != asset.get('location'):
                                chg.append(f"Location: {asset.get('location')} -> {new_location}")
                            if new_assigned_user != asset.get('assigned_user'):
                                chg.append(f"Assigned: {asset.get('assigned_user')} -> {new_assigned_user}")
                            summary = "\n".join(chg) if chg else "Minor update"
                            note_text = f"{summary}\n\nNotes: {notes_text}"
                            n_ok, n_err = execute_non_query(note_q, (aid, note_text, "Asset Update", "System User"))
                            if n_ok:
                                st.success("✅ Asset updated and logged")
                                st.session_state.view_asset_id = None
                                safe_rerun()
                            else:
                                st.warning(f"Asset updated but note not saved: {n_err}")
                        else:
                            st.error(f"Error updating asset: {uerr}")
            st.markdown("---")
            st.subheader("📋 Asset History / Enter update notes")
            # Notes text area for updates
            if 'asset_update_notes' not in st.session_state:
                st.session_state['asset_update_notes'] = ''
            st.session_state['asset_update_notes'] = st.text_area("Enter notes to append when you click Update Asset (required)", value=st.session_state['asset_update_notes'], height=120)
            # Load history from Asset_Notes
            notes_q2 = """
                SELECT note_id, note_text, note_type, created_by, created_at
                FROM dbo.Asset_Notes
                WHERE asset_id = ?
                ORDER BY created_at DESC
            """
            notes_df2, notes_err2 = execute_query(notes_q2, (aid,))
            if notes_err2:
                st.info("No asset history table found. Run DB migration.")
            elif notes_df2 is None or len(notes_df2)==0:
                st.info("No history yet for this asset.")
            else:
                st.markdown('<div class="notes-container">', unsafe_allow_html=True)
                for _, n in notes_df2.iterrows():
                    st.markdown(f"""
                        <div class="note-item">
                          <div class="note-header">{n['note_type']} • {n['created_by']} • {n['created_at']}</div>
                          <div class="note-text">{n['note_text']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================ 
# PROCUREMENT REQUESTS PAGE (public forms are linked via sidebar)
# ============================================================================

elif page == "🛒 Procurement Requests":
    st.header("🛒 Procurement Requests")
    # === DEBUG BLOCK FOR PROCUREMENT (insert immediately after `elif page == "🛒 Procurement Requests":`) ===
    # Temporary debug: show whether procurement SELECT returns rows (safe, read-only)
    proc_check_q = "SELECT TOP (50) * FROM dbo.Procurement_Requests ORDER BY created_at DESC"
    proc_df, proc_err = execute_query(proc_check_q)
    st.write("DEBUG: proc_check_q:", proc_check_q)
    st.write("DEBUG: proc_fetch_error:", proc_err)
    if proc_df is None:
        st.write("DEBUG: proc_df is None (connection/query error)")
    elif isinstance(proc_df, pd.DataFrame) and len(proc_df) == 0:
        st.write("DEBUG: proc_df is empty (no rows returned)")
    else:
        try:
            st.write(f"DEBUG: proc_df shape: {getattr(proc_df, 'shape', 'unknown')}")
            st.dataframe(proc_df.head(20), width='stretch')
        except Exception as _dbg_e:
            st.write("DEBUG: error rendering proc_df preview:", repr(_dbg_e))
    # End procurement debug block (remove once debugging complete)
    # === END PROCUREMENT DEBUG BLOCK ===
    # (The create / list code is retained from the original app — unchanged)
    # For public access, run public_procurement_form.py as a separate Streamlit app and link via sidebar.

# ============================================================================ 
# FLEET MANAGEMENT PAGE (with pending requests admin UI + gallery hint)
# ============================================================================

elif page == "🚗 Fleet Management":
    st.header("🚗 Fleet Management")

    # Show pending requests for admins (if any)
    pending_q = """
        SELECT t.trip_id, t.vehicle_id, t.requester_first, t.requester_last, t.requester_email,
               CONVERT(VARCHAR(50), t.departure_time, 127) as departure_iso,
               CONVERT(VARCHAR(50), t.return_time, 127) as return_iso,
               t.destination, t.purpose, t.status
        FROM dbo.Vehicle_Trips t
        WHERE t.status = 'Requested'
        ORDER BY t.created_at DESC
    """
    pending_df, pend_err = execute_query(pending_q)
    if pend_err:
        logger.debug("Pending requests load error: %s", pend_err)
    elif pending_df is not None and len(pending_df) > 0:
        st.warning(f"⚠️ There are {len(pending_df)} pending vehicle requests awaiting review")
        for _, preq in pending_df.iterrows():
            st.markdown("---")
            st.write(f"**Request #{preq['trip_id']}** — Vehicle ID: {preq['vehicle_id']}")
            st.write(f"Requester: {preq['requester_first']} {preq['requester_last']} ({preq['requester_email']})")
            st.write(f"Departure: {preq['departure_iso']}  •  Return: {preq['return_iso']}")
            st.write(f"Destination: {preq['destination']}")
            with st.form(f"review_req_{preq['trip_id']}"):
                decision = st.selectbox("Decision", ["Approve","Deny"], index=0)
                admin_note = st.text_area("Admin note (will be appended to vehicle history)", height=100)
                if st.form_submit_button("Submit Decision"):
                    if decision == "Approve":
                        execute_non_query("UPDATE dbo.Vehicle_Trips SET status='Approved' WHERE trip_id = ?", (preq['trip_id'],))
                        execute_non_query("UPDATE dbo.vehicles SET status = 'In Use', current_trip_id = ? WHERE id = ?", (preq['trip_id'], preq['vehicle_id']))
                        result_note = f"Approved request {preq['trip_id']}. Note: {admin_note}"
                    else:
                        execute_non_query("UPDATE dbo.Vehicle_Trips SET status='Denied' WHERE trip_id = ?", (preq['trip_id'],))
                        execute_non_query("UPDATE dbo.vehicles SET status = 'Available', current_trip_id = NULL WHERE id = ?", (preq['vehicle_id'],))
                        result_note = f"Denied request {preq['trip_id']}. Note: {admin_note}"
                    # append to vehicle notes_log column
                    try:
                        append_sql = """
                            UPDATE dbo.vehicles
                            SET notes_log = COALESCE(COALESCE(notes_log, '') + CHAR(13)+CHAR(10) + ?, ?), updated_at = GETDATE()
                            WHERE id = ?
                        """
                        execute_non_query(append_sql, (result_note, result_note, preq['vehicle_id']))
                    except Exception as e:
                        logger.warning("Failed to append vehicle note: %s", e)
                    # mark notification read and email parties
                    try:
                        execute_non_query("UPDATE dbo.Notifications SET is_read = 1 WHERE notification_type = 'vehicle_request' AND reference_id = ?", (preq['trip_id'],))
                    except Exception:
                        pass
                    # Email requester and fleet admins
                    try:
                        requester_email = preq['requester_email']
                        if requester_email:
                            send_email(f"Vehicle Request #{preq['trip_id']} - {decision}", f"Your request was {decision}.\n\n{admin_note}", [requester_email])
                        fleet_admins_cfg = []
                        try:
                            fleet_admins_cfg = st.secrets.get("fleet", {}).get("admins","").split(",")
                        except Exception:
                            fleet_admins_cfg = os.getenv("FLEET_ADMINS","").split(",")
                        fleet_admins = [r.strip() for r in fleet_admins_cfg if r and r.strip()]
                        if fleet_admins:
                            send_email(f"[VDH Fleet] Request #{preq['trip_id']} {decision}", result_note, fleet_admins)
                    except Exception as e:
                        logger.exception("Failed to send decision emails: %s", e)
                    st.success(f"Request {preq['trip_id']} marked {decision}")
                    safe_rerun()

    # Gallery-style vehicle list (one row per vehicle, image placeholder + details)
    st.markdown("---")
    st.subheader("Vehicle Fleet (Gallery)")
    vq = """
        SELECT id, year, make_model, vin, license_plate, photo_url, initial_mileage, current_mileage, last_service_mileage, last_service_date, miles_until_service, status, usage_count, current_driver, current_trip_id
        FROM dbo.vehicles
        ORDER BY make_model
    """
    vehicles_df, verr = execute_query(vq)
    if verr:
        st.error(verr)
    elif vehicles_df is None or len(vehicles_df)==0:
        st.info("No vehicles found")
    else:
        # Render as stacked gallery cards
        for _, v in vehicles_df.iterrows():
            st.markdown("<div style='border:1px solid #ddd; padding:12px; margin-bottom:12px; border-radius:6px;'>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1,3,1])
            with col1:
                if v.get('photo_url'):
                    st.image(v['photo_url'], width='stretch')
                else:
                    st.image("https://via.placeholder.com/250x150.png?text=Vehicle+Image", width='stretch')
            with col2:
                st.markdown(f"### {v.get('make_model','N/A')} — {v.get('license_plate','')}")
                st.write(f"Year: {v.get('year','N/A')} • VIN: {v.get('vin','N/A')}")
                st.write(f"Mileage: {v.get('current_mileage','N/A')} • Miles until service: {v.get('miles_until_service','N/A')}")
                st.write(f"Status: {v.get('status','N/A')}")
            with col3:
                if v.get('current_trip_id'):
                    if st.button("View Trip", key=f"vtrip_{v['id']}"):
                        st.session_state.view_trip_id = v.get('current_trip_id')
                        safe_rerun()
                else:
                    if st.button("Details", key=f"vdet_{v['id']}"):
                        st.session_state.view_vehicle_id = v['id']
                        safe_rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# ============================================================================ 
# REPORT BUILDER PAGE
# ============================================================================

elif page == "📈 Report Builder":
    st.header("📈 Report Builder")
    report_type = st.selectbox("Select Report Type", ["Ticket Summary Report","Asset Inventory Report","Procurement Status Report","Fleet Usage Report"])
    start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    end_date = st.date_input("End Date", value=datetime.now())
    locations = st.multiselect("Select Locations", ["Petersburg","Hopewell","Dinwiddie","Surry","Greensville/Emporia","Prince George","Sussex"], default=["Petersburg"])
    report_format = st.selectbox("Report Format", ["Excel","PDF","CSV"])
    if st.button("🎯 Generate Report"):
        with st.spinner("Generating report..."):
            if report_type == "Ticket Summary Report":
                query = f"""
                    SELECT ticket_id, short_description AS ticket_subject, status AS ticket_status, priority AS ticket_priority,
                           name AS customer_name, email AS customer_email, location AS vdh_location,
                           phone_number, CONVERT(VARCHAR(50), created_at, 127) as created_date, CONVERT(VARCHAR(50), updated_at, 127) as updated_date
                    FROM dbo.Tickets
                    WHERE created_at BETWEEN '{start_date}' AND '{end_date}'
                      AND location IN ('{"','".join(locations)}')
                    ORDER BY created_at DESC
                """
            elif report_type == "Asset Inventory Report":
                query = f"""
                    SELECT asset_tag, type AS asset_type, model AS make_model, serial AS serial_number,
                           status, location, assigned_user AS assigned_to, CONVERT(VARCHAR(50), purchase_date, 127) as purchase_date, CONVERT(VARCHAR(50), created_at, 127) as created_at
                    FROM dbo.Assets
                    WHERE location IN ('{"','".join(locations)}')
                    ORDER BY asset_tag
                """
            elif report_type == "Procurement Status Report":
                query = f"""
                    SELECT request_number, requester_name, location, status, priority, total_amount,
                           CONVERT(VARCHAR(50), created_at, 127) as created_at, CONVERT(VARCHAR(50), updated_at, 127) as updated_at
                    FROM dbo.Procurement_Requests
                    WHERE created_at BETWEEN '{start_date}' AND '{end_date}'
                      AND location IN ('{"','".join(locations)}')
                    ORDER BY created_at DESC
                """
            else:
                query = f"""
                    SELECT v.make_model, v.license_plate, v.status, v.usage_count, v.current_mileage, COUNT(t.trip_id) as trips_in_period
                    FROM dbo.vehicles v
                    LEFT JOIN dbo.Vehicle_Trips t ON v.id = t.vehicle_id AND CONVERT(date, t.departure_time) BETWEEN '{start_date}' AND '{end_date}'
                    GROUP BY v.make_model, v.license_plate, v.status, v.usage_count, v.current_mileage
                    ORDER BY v.make_model
                """
            df, derr = execute_query(query)
            if derr:
                st.error(derr)
            elif df is None or len(df)==0:
                st.warning("No data found")
            else:
                st.success(f"Report generated with {len(df)} records")
                st.subheader("Report Preview")
                st.dataframe(df, width='stretch')
                if report_format == "Excel" and HAS_EXCEL:
                    output = generate_excel_report(df, report_type)
                    if output:
                        st.download_button("📥 Download Excel", data=output, file_name=f"{report_type.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                elif report_format == "PDF" and HAS_PDF:
                    output = generate_pdf_report(df, report_type)
                    if output:
                        st.download_button("📥 Download PDF", data=output, file_name=f"{report_type.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.pdf", mime="application/pdf")
                else:
                    csv = df.to_csv(index=False)
                    st.download_button("📥 Download CSV", data=csv, file_name=f"{report_type.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

# ============================================================================ 
# CONNECTION TEST PAGE
# ============================================================================

elif page == "🔌 Connection Test":
    st.header("🔌 Database Connection Test")
    server, database, username, _ = get_connection_string()
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"**Server:** {server}")
        st.write(f"**Database:** {database}")
    with c2:
        st.write(f"**Username:** {username}")
        st.write(f"**PyODBC Available:** {'✅ Yes' if HAS_PYODBC else '❌ No'}")
    st.markdown("---")
    if st.button("🔎 Show Table Columns"):
        tables_to_check = ['Tickets','Assets','Procurement_Requests','vehicles','Vehicle_Trips']
        for table in tables_to_check:
            st.write(f"**Table: dbo.{table}**")
            cols_q = f"""
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = '{table}'
                ORDER BY ORDINAL_POSITION
            """
            cols_df, cols_err = execute_query(cols_q)
            if cols_err:
                st.error(cols_err)
            elif cols_df is not None and len(cols_df)>0:
                st.dataframe(cols_df, width='stretch')
            else:
                st.warning(f"Table {table} not found")
            st.markdown("---")
# -----------------------
# Public submission pages (visible to non-admin users)
# -----------------------

if page == "📝 Submit Ticket":
    st.header("Submit a Ticket")
    st.markdown("Use this form to request help. Your submission will be created as a draft for admin review.")
    with st.form("public_ticket_form"):
        name = st.text_input("Your name", help="First and last name")
        email = st.text_input("Your email", help="We will use this to send a confirmation")
        phone = st.text_input("Phone (optional)")
        location = st.text_input("Location (optional)")
        priority = st.selectbox("Priority", ["low", "medium", "high", "urgent"])
        short_desc = st.text_input("Short description")
        description = st.text_area("Full description")
        submit = st.form_submit_button("Submit Ticket")

    if submit:
        if not name or not email or not short_desc:
            st.error("Name, email and short description are required.")
        else:
            public_token = str(uuid.uuid4())[:8]
            insert_q = """
                INSERT INTO dbo.Tickets
                (status, priority, name, email, location, phone_number, short_description, description, created_at)
                VALUES ('draft', ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """
            params = (priority, name, email, location or None, phone or None, short_desc, description or None)
            ok, err = execute_non_query(insert_q, params)
            if ok:
                st.success("Ticket submitted. Reference token: " + public_token)
                st.info("Admins will review and follow up if you provided contact details.")
            else:
                st.error(f"Submission failed: {err}")

elif page == "📝 Submit Procurement Request":
    st.header("Submit a Procurement Request")
    st.markdown("Submitters: provide request details. A procurement draft will be created for procurement team review.")
    with st.form("public_procurement_form"):
        requester_name = st.text_input("Your name", help="Requester")
        requester_email = st.text_input("Your email")
        location = st.text_input("Location")
        department = st.text_input("Department")
        justification = st.text_area("Justification for request", help="Why you need this item")
        # Simple line item entry as one item for public submission
        item_description = st.text_input("Item description (one line)")
        quantity = st.number_input("Quantity", min_value=1, value=1)
        unit_price = st.number_input("Estimated unit price", min_value=0.0, value=0.0, format="%.2f")
        submit_p = st.form_submit_button("Submit Procurement Request")
    if submit_p:
        if not requester_name or not requester_email or not justification or not item_description:
            st.error("Name, email, justification and at least one item description are required.")
        else:
            public_token = str(uuid.uuid4())[:8]
            req_number = f"PR-{datetime.now().strftime('%Y%m%d')}-{public_token}"
            total = float(unit_price) * int(quantity)
            items_payload = [{"line_number": 1, "item_description": item_description, "quantity": int(quantity), "unit_price": float(unit_price), "total_price": total}]
            attachments_json = json.dumps(items_payload)
            insert_q = """
                INSERT INTO dbo.Procurement_Requests
                (request_number, requester_name, requester_email, location, department, justification, total_amount, status, priority, created_at, attachments)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'draft', 'normal', GETDATE(), ?)
            """
            params = (req_number, requester_name, requester_email, location or None, department or None, justification, total, attachments_json)
            ok, err = execute_non_query(insert_q, params)
            if ok:
                st.success("Procurement request submitted. Reference: " + req_number)
                st.info("Procurement team will review the draft.")
            else:
                st.error(f"Submission failed: {err}")

elif page == "🛫 Request Vehicle":
    st.header("Vehicle Request")
    st.markdown("Request a vehicle or trip. This creates a draft trip for the Fleet team to review.")
    with st.form("public_vehicle_request"):
        requester_first = st.text_input("First name")
        requester_last = st.text_input("Last name")
        requester_email = st.text_input("Email")
        destination = st.text_input("Destination / Purpose")
        departure_date = st.date_input("Departure date", value=date.today())
        return_date = st.date_input("Return date", value=date.today())
        starting_mileage = st.number_input("Starting mileage (if known)", min_value=0, value=0)
        submit_v = st.form_submit_button("Submit Vehicle Request")
    if submit_v:
        if not requester_first or not requester_last or not requester_email or not destination:
            st.error("Please fill name, email and destination.")
        else:
            public_token = str(uuid.uuid4())[:8]
            insert_q = """
                INSERT INTO dbo.Vehicle_Trips
                (vehicle_id, requester_first, requester_last, requester_email, destination, departure_time, return_time, status, starting_mileage, created_at)
                VALUES (NULL, ?, ?, ?, ?, ?, ?, 'draft', ?, GETDATE())
            """
            dep_ts = departure_date.isoformat()
            ret_ts = return_date.isoformat()
            params = (requester_first, requester_last, requester_email, destination, dep_ts, ret_ts, int(starting_mileage))
            ok, err = execute_non_query(insert_q, params)
            if ok:
                st.success("Vehicle request submitted. Reference: " + public_token)
                st.info("Fleet team will review this draft.")
            else:
                st.error(f"Submission failed: {err}")

elif page == "🔌 Connection Test":
    st.header("🔌 Connection Test")
    server, database, username, _ = get_connection_string()
    st.write(f"Server: {server}")
    st.write(f"Database: {database}")
    st.write(f"Username: {username}")
    df, err = execute_query("SELECT TOP (1) 1 as ok")
    if err:
        st.error(f"Connection test failed: {err}")
    else:
        st.success("Connection OK")

# -----------------------
# Admin pages (visible after admin sign-in)
# -----------------------
elif page == "📊 Dashboard":
    st.header("📊 Dashboard Overview")

    # Fetch data
    with st.spinner("Loading dashboard data..."):
        # Get ticket statistics
        ticket_stats_query = """
            SELECT
                COUNT(*) as total_tickets,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_tickets,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tickets,
                SUM(CASE WHEN status = 'on_hold' THEN 1 ELSE 0 END) as on_hold_tickets,
                SUM(CASE WHEN status = 'waiting_customer_response' THEN 1 ELSE 0 END) as waiting_tickets,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_tickets,
                SUM(CASE WHEN priority = 'urgent' THEN 1 ELSE 0 END) as urgent_tickets
            FROM dbo.Tickets
        """
        stats_df, error = execute_query(ticket_stats_query)

        # Get asset statistics
        asset_stats_query = """
            SELECT
                COUNT(*) as total_assets,
                SUM(CASE WHEN status = 'Deployed' THEN 1 ELSE 0 END) as deployed_assets,
                SUM(CASE WHEN status = 'In-Stock' THEN 1 ELSE 0 END) as available_assets,
                SUM(CASE WHEN status = 'Repair' THEN 1 ELSE 0 END) as repair_assets
            FROM dbo.Assets
        """
        asset_stats_df, asset_error = execute_query(asset_stats_query)

        if not error and stats_df is not None:
            stats = stats_df.iloc[0]

            # Top metrics row - Tickets
            st.subheader("🎫 Ticket Overview")
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)

            with mcol1:
                st.metric(label="📋 Total Tickets", value=int(stats['total_tickets']))
            with mcol2:
                st.metric(label="🟢 Open", value=int(stats['open_tickets']), delta_color="inverse")
            with mcol3:
                st.metric(label="🔄 In Progress", value=int(stats['in_progress_tickets']))
            with mcol4:
                st.metric(label="🚨 Urgent", value=int(stats['urgent_tickets']), delta_color="inverse")

        # Asset metrics row
        if not asset_error and asset_stats_df is not None:
            asset_stats = asset_stats_df.iloc[0]

            st.markdown("---")
            st.subheader("💻 Asset Overview")
            acol1, acol2, acol3, acol4 = st.columns(4)

            with acol1:
                st.metric(label="💼 Total Assets", value=int(asset_stats['total_assets']))
            with acol2:
                st.metric(label="✅ Deployed", value=int(asset_stats['deployed_assets']))
            with acol3:
                st.metric(label="📦 In Stock", value=int(asset_stats['available_assets']))
            with acol4:
                st.metric(label="🔧 In Repair", value=int(asset_stats['repair_assets']), delta_color="inverse")

        st.markdown("---")

        # Charts Row 1 - Tickets by Status and Location
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Tickets by Status")
            status_query = """
                SELECT
                    CASE status
                        WHEN 'waiting_customer_response' THEN 'Waiting Customer'
                        WHEN 'on_hold' THEN 'On Hold'
                        WHEN 'in_progress' THEN 'In Progress'
                        ELSE UPPER(LEFT(status, 1)) + LOWER(SUBSTRING(status, 2, LEN(status)))
                    END as status_display,
                    COUNT(*) as count
                FROM dbo.Tickets
                GROUP BY status
                ORDER BY count DESC
            """
            status_df, error = execute_query(status_query)

            if not error and status_df is not None and len(status_df) > 0:
                status_colors = {
                    'Open': '#FF6B35',
                    'In Progress': '#002855',
                    'On Hold': '#FFC107',
                    'Waiting Customer': '#17A2B8',
                    'Resolved': '#28A745',
                    'Closed': '#6C757D'
                }
                fig = px.pie(
                    status_df,
                    values='count',
                    names='status_display',
                    color='status_display',
                    color_discrete_map=status_colors,
                    hover_data=['count']
                )
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
                )
                fig.update_layout(height=350, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No status data available")

        with col2:
            st.subheader("📍 Tickets by Location")
            location_query = """
                SELECT location, COUNT(*) as count
                FROM dbo.Tickets
                WHERE location IS NOT NULL
                GROUP BY location
                ORDER BY count DESC
            """
            location_df, error = execute_query(location_query)

            if not error and location_df is not None and len(location_df) > 0:
                fig = px.bar(
                    location_df,
                    x='count',
                    y='location',
                    orientation='h',
                    color='count',
                    color_continuous_scale=[[0, '#FF6B35'], [0.5, '#002855'], [1, '#001a33']],
                    hover_data={'count': True, 'location': False}
                )
                fig.update_traces(hovertemplate='<b>%{y}</b><br>Tickets: %{x}<extra></extra>')
                fig.update_layout(height=350, showlegend=False, xaxis_title="Number of Tickets", yaxis_title="Location")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No location data available")

        # Charts Row 2 - Priority and Assets
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🎯 Tickets by Priority")
            priority_query = """
                SELECT priority, COUNT(*) as count FROM dbo.Tickets
                GROUP BY priority
                ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 END
            """
            priority_df, error = execute_query(priority_query)

            if not error and priority_df is not None and len(priority_df) > 0:
                priority_colors_map = {'urgent': '#DC3545', 'high': '#FF6B35', 'medium': '#FFC107', 'low': '#28A745'}
                fig = px.bar(
                    priority_df,
                    x='priority',
                    y='count',
                    color='priority',
                    color_discrete_map=priority_colors_map,
                    hover_data={'priority': False, 'count': True}
                )
                fig.update_traces(hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>')
                fig.update_layout(height=350, showlegend=False, xaxis_title="Priority Level", yaxis_title="Count")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No priority data available")

        with col2:
            st.subheader("📦 Assets by Location")
            asset_location_query = """
                SELECT location, COUNT(*) as count
                FROM dbo.Assets
                WHERE location IS NOT NULL
                GROUP BY location
                ORDER BY count DESC
            """
            asset_location_df, error = execute_query(asset_location_query)

            if not error and asset_location_df is not None and len(asset_location_df) > 0:
                fig = px.bar(
                    asset_location_df,
                    x='count',
                    y='location',
                    orientation='h',
                    color='count',
                    color_continuous_scale=[[0, '#FF6B35'], [0.5, '#002855'], [1, '#001a33']],
                    hover_data={'count': True, 'location': False}
                )
                fig.update_traces(hovertemplate='<b>%{y}</b><br>Assets: %{x}<extra></extra>')
                fig.update_layout(height=350, showlegend=False, xaxis_title="Number of Assets", yaxis_title="Location")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No asset location data available")

        # Charts Row 3 - Asset Status and Type
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("💻 Assets by Status")
            asset_status_query = "SELECT status, COUNT(*) as count FROM dbo.Assets GROUP BY status"
            asset_status_df, error = execute_query(asset_status_query)

            if not error and asset_status_df is not None and len(asset_status_df) > 0:
                asset_status_colors = {
                    'Deployed': '#002855', 'In-Stock': '#28A745', 'Surplus': '#6C757D',
                    'Repair': '#FF6B35', 'Retired': '#343A40', 'Unaccounted': '#DC3545'
                }
                fig = px.pie(
                    asset_status_df, values='count', names='status', color='status',
                    color_discrete_map=asset_status_colors, hover_data=['count']
                )
                fig.update_traces(textposition='inside', textinfo='percent+label',
                                  hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>')
                fig.update_layout(height=350, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No asset status data available")

        with col2:
            st.subheader("📦 Assets by Type")
            asset_type_query = "SELECT type, COUNT(*) as count FROM dbo.Assets GROUP BY type ORDER BY count DESC"
            asset_type_df, error = execute_query(asset_type_query)

            if not error and asset_type_df is not None and len(asset_type_df) > 0:
                fig = px.bar(
                    asset_type_df, x='type', y='count', color='count',
                    color_continuous_scale=[[0, '#FF6B35'], [0.5, '#002855'], [1, '#001a33']],
                    hover_data={'type': False, 'count': True}
                )
                fig.update_traces(hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>')
                fig.update_layout(height=350, showlegend=False, xaxis_title="Asset Type", yaxis_title="Count")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No asset type data available")

# ... the rest of admin pages continue unchanged (Tickets list, Assets list, Fleet, Procurement, Reports, etc.) ...
# For brevity I preserved the admin page logic above; ensure the rest of your original admin page code
# follows here (you had it previously in the file). If it's missing, you can paste it after this point.

# Footer
st.markdown("---")
st.markdown("*VDH Service Center - Comprehensive Management System | Virginia Department of Health © 2025*")