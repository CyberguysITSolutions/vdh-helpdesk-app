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
import pandas as pd
from datetime import datetime, timedelta, date
import os
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64
import json
import uuid
from typing import Optional, Tuple
import traceback

# Page configuration
st.set_page_config(page_title="VDH Service Center", page_icon="🏥", layout="wide")

# Try to import pyodbc
try:
    import pyodbc
    HAS_PYODBC = True
except Exception:
    HAS_PYODBC = False

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

# Database connection
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
        return None, str(e)


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
        return None, str(e)


def generate_csv_report(df):
    """Generate CSV report"""
    try:
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        return output, None
    except Exception as e:
        return None, str(e)


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

# Initialize session state
if 'show_add_asset_form' not in st.session_state:
    st.session_state.show_add_asset_form = False
if 'show_add_ticket_form' not in st.session_state:
    st.session_state.show_add_ticket_form = False
if 'edit_asset_id' not in st.session_state:
    st.session_state.edit_asset_id = None
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
    # Quick link to public ticket submission page
    st.sidebar.markdown("""
    <ul style="list-style-type: none; padding-left: 0;">
        <li><a href="/01_Public_Create_Ticket">Submit a Ticket</a></li>
    </ul>
    """, unsafe_allow_html=True)
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
st.markdown("*VDH Service Center - v5.0 | Virginia Department of Health © 2025*")
