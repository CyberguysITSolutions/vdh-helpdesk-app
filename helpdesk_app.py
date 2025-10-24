import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64

# Page configuration
st.set_page_config(page_title="VDH Service Center", page_icon="🏥", layout="wide")

# Try to import pyodbc
try:
    import pyodbc
    HAS_PYODBC = True
except:
    HAS_PYODBC = False

# Try to import reporting libraries
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils.dataframe import dataframe_to_rows
    HAS_EXCEL = True
except:
    HAS_EXCEL = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.units import inch
    HAS_PDF = True
except:
    HAS_PDF = False

# Database connection
@st.cache_resource
def get_connection_string():
    try:
        server = st.secrets["database"]["server"]
        database = st.secrets["database"]["database"]
        username = st.secrets["database"]["username"]
        password = st.secrets["database"]["password"]
    except:
        server = os.getenv("DB_SERVER")
        database = os.getenv("DB_DATABASE")
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
    
    return server, database, username, password

def execute_query(query, params=None):
    if not HAS_PYODBC:
        return None, "pyodbc not installed"
    
    server, database, username, password = get_connection_string()
    
    try:
        conn_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;"
        conn = pyodbc.connect(conn_string, timeout=30)
        
        if params:
            df = pd.read_sql(query, conn, params=params)
        else:
            df = pd.read_sql(query, conn)
        
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)

def execute_non_query(query, params=None):
    """Execute INSERT, UPDATE, DELETE queries"""
    if not HAS_PYODBC:
        return False, "pyodbc not installed"
    
    server, database, username, password = get_connection_string()
    
    try:
        conn_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;"
        conn = pyodbc.connect(conn_string, timeout=30)
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        conn.commit()
        cursor.close()
        conn.close()
        return True, None
    except Exception as e:
        return False, str(e)

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
                except:
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

# Header with VDH Logo
col1, col2, col3 = st.columns([1, 4, 1])
with col1:
    try:
        st.image("VDH-logo.png", width=120)
    except:
        st.markdown("### 🏥")
with col2:
    st.markdown("<h1 style='color: #002855; margin-top: 20px;'>Service Center</h1>", unsafe_allow_html=True)
with col3:
    st.markdown("<p style='text-align: right; margin-top: 30px;'><strong>Admin</strong></p>", unsafe_allow_html=True)

st.markdown("---")

# Sidebar navigation
page = st.sidebar.selectbox("Navigate", [
    "📊 Dashboard", 
    "🎫 Tickets",
    "💻 Assets",
    "🛒 Procurement",
    "📈 Reports",
    "👥 Users", 
    "🔍 Query Builder", 
    "🔌 Connection Test"
])

if page == "📊 Dashboard":
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
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(label="📋 Total Tickets", value=int(stats['total_tickets']))
            with col2:
                st.metric(label="🟢 Open", value=int(stats['open_tickets']), delta_color="inverse")
            with col3:
                st.metric(label="🔄 In Progress", value=int(stats['in_progress_tickets']))
            with col4:
                st.metric(label="🚨 Urgent", value=int(stats['urgent_tickets']), delta_color="inverse")
        
        # Asset metrics row
        if not asset_error and asset_stats_df is not None:
            asset_stats = asset_stats_df.iloc[0]
            
            st.markdown("---")
            st.subheader("💻 Asset Overview")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(label="💼 Total Assets", value=int(asset_stats['total_assets']))
            with col2:
                st.metric(label="✅ Deployed", value=int(asset_stats['deployed_assets']))
            with col3:
                st.metric(label="📦 In Stock", value=int(asset_stats['available_assets']))
            with col4:
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
                # VDH color scheme for status
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
                fig.update_traces(
                    hovertemplate='<b>%{y}</b><br>Tickets: %{x}<extra></extra>'
                )
                fig.update_layout(
                    height=350,
                    showlegend=False,
                    xaxis_title="Number of Tickets",
                    yaxis_title="Location",
                    coloraxis_showscale=False
                )
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
                # VDH colors for priority
                priority_colors_map = {
                    'urgent': '#DC3545',
                    'high': '#FF6B35', 
                    'medium': '#FFC107',
                    'low': '#28A745'
                }
                fig = px.bar(
                    priority_df, 
                    x='priority', 
                    y='count',
                    color='priority',
                    color_discrete_map=priority_colors_map,
                    hover_data={'priority': False, 'count': True}
                )
                fig.update_traces(
                    hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
                )
                fig.update_layout(
                    height=350,
                    showlegend=False,
                    xaxis_title="Priority Level",
                    yaxis_title="Count"
                )
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
                fig.update_traces(
                    hovertemplate='<b>%{y}</b><br>Assets: %{x}<extra></extra>'
                )
                fig.update_layout(
                    height=350,
                    showlegend=False,
                    xaxis_title="Number of Assets",
                    yaxis_title="Location",
                    coloraxis_showscale=False
                )
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
                # VDH colors for asset status
                asset_status_colors = {
                    'Deployed': '#002855',
                    'In-Stock': '#28A745',
                    'Surplus': '#6C757D',
                    'Repair': '#FF6B35',
                    'Retired': '#343A40',
                    'Unaccounted': '#DC3545'
                }
                fig = px.pie(
                    asset_status_df, 
                    values='count', 
                    names='status',
                    color='status',
                    color_discrete_map=asset_status_colors,
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
                st.info("No asset status data available")
        
        with col2:
            st.subheader("📦 Assets by Type")
            asset_type_query = "SELECT type, COUNT(*) as count FROM dbo.Assets GROUP BY type ORDER BY count DESC"
            asset_type_df, error = execute_query(asset_type_query)
            
            if not error and asset_type_df is not None and len(asset_type_df) > 0:
                fig = px.bar(
                    asset_type_df, 
                    x='type', 
                    y='count',
                    color='count',
                    color_continuous_scale=[[0, '#FF6B35'], [0.5, '#002855'], [1, '#001a33']],
                    hover_data={'type': False, 'count': True}
                )
                fig.update_traces(
                    hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
                )
                fig.update_layout(
                    height=350,
                    showlegend=False,
                    xaxis_title="Asset Type",
                    yaxis_title="Count",
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No asset type data available")

elif page == "🛒 Procurement":
    st.header("🛒 Procurement Management")
    
    # Initialize procurement session states
    if 'show_create_procurement' not in st.session_state:
        st.session_state.show_create_procurement = False
    if 'view_procurement_id' not in st.session_state:
        st.session_state.view_procurement_id = None
    if 'procurement_items' not in st.session_state:
        st.session_state.procurement_items = []
    
    # Check if procurement tables exist
    check_table_query = """
        SELECT COUNT(*) as table_count
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'dbo' 
        AND TABLE_NAME = 'Procurement_Requests'
    """
    table_check, error = execute_query(check_table_query)
    
    if error or table_check is None or table_check.iloc[0]['table_count'] == 0:
        st.warning("⚠️ Procurement system not set up yet. Please run the setup SQL script.")
        st.markdown("""
        ### Setup Required:
        1. Download: `setup_procurement_system.sql`
        2. Run in Azure SQL Query Editor
        3. Refresh this page
        
        [View Setup Instructions](https://github.com/your-repo)
        """)
    else:
        # Procurement is set up - show interface
        
        # Back button if viewing details
        if st.session_state.view_procurement_id:
            if st.button("← Back to Procurement List"):
                st.session_state.view_procurement_id = None
                st.rerun()
            
            st.markdown("---")
            
            # Load procurement request details
            proc_query = f"""
                SELECT pr.*, 
                    CONCAT(a1.first_name, ' ', a1.last_name) as level1_approver,
                    CONCAT(a2.first_name, ' ', a2.last_name) as level2_approver
                FROM dbo.Procurement_Requests pr
                LEFT JOIN dbo.Procurement_Approvers a1 ON pr.level1_approver_id = a1.approver_id
                LEFT JOIN dbo.Procurement_Approvers a2 ON pr.level2_approver_id = a2.approver_id
                WHERE pr.request_id = {st.session_state.view_procurement_id}
            """
            proc_df, error = execute_query(proc_query)
            
            if error or proc_df is None or len(proc_df) == 0:
                st.error("Procurement request not found")
                st.session_state.view_procurement_id = None
            else:
                proc = proc_df.iloc[0]
                
                # Header
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.subheader(f"Request {proc['request_number']}")
                with col2:
                    status_colors = {
                        'draft': '⚪', 'pending_level1': '🟠', 'pending_level2': '🔵',
                        'approved': '🟢', 'rejected': '🔴', 'ordered': '🔵', 
                        'received': '🟢', 'cancelled': '⚫'
                    }
                    st.write(f"{status_colors.get(proc['status'], '⚪')} Status: **{proc['status'].upper()}**")
                with col3:
                    priority_colors = {'low': '🟢', 'normal': '⚪', 'high': '🟠', 'urgent': '🔴'}
                    st.write(f"{priority_colors.get(proc['priority'], '⚪')} Priority: **{proc['priority'].upper()}**")
                
                st.markdown("---")
                
                # Request Details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📋 Request Information")
                    st.write(f"**Request Date:** {proc['request_date']}")
                    st.write(f"**Requester:** {proc['requester_name']}")
                    st.write(f"**Email:** {proc['requester_email']}")
                    if proc['requester_phone']:
                        st.write(f"**Phone:** {proc['requester_phone']}")
                    st.write(f"**Location:** {proc['location']}")
                    if proc['department']:
                        st.write(f"**Department:** {proc['department']}")
                
                with col2:
                    st.subheader("💰 Financial Information")
                    st.write(f"**Total Amount:** ${proc['total_amount']:,.2f}")
                    if proc['cst_code']:
                        st.write(f"**CST Code:** {proc['cst_code']}")
                    if proc['coa_code']:
                        st.write(f"**COA Code:** {proc['coa_code']}")
                    if proc['prog_code']:
                        st.write(f"**PROG Code:** {proc['prog_code']}")
                    if proc['fund_code']:
                        st.write(f"**FUND Code:** {proc['fund_code']}")
                
                st.markdown("---")
                
                # Vendor Information
                if proc['vendor_name']:
                    st.subheader("🏢 Vendor Information")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Vendor:** {proc['vendor_name']}")
                        if proc['vendor_contact']:
                            st.write(f"**Contact:** {proc['vendor_contact']}")
                    with col2:
                        if proc['vendor_phone']:
                            st.write(f"**Phone:** {proc['vendor_phone']}")
                        if proc['vendor_email']:
                            st.write(f"**Email:** {proc['vendor_email']}")
                    st.markdown("---")
                
                # Line Items
                st.subheader("📦 Line Items")
                items_query = f"""
                    SELECT * FROM dbo.Procurement_Items 
                    WHERE request_id = {st.session_state.view_procurement_id}
                    ORDER BY line_number
                """
                items_df, error = execute_query(items_query)
                
                if not error and items_df is not None and len(items_df) > 0:
                    # Display as formatted table
                    display_df = items_df[['line_number', 'item_description', 'quantity', 'unit_price', 'total_price']].copy()
                    display_df.columns = ['#', 'Description', 'Qty', 'Unit Price', 'Total']
                    display_df['Unit Price'] = display_df['Unit Price'].apply(lambda x: f"${x:,.2f}")
                    display_df['Total'] = display_df['Total'].apply(lambda x: f"${x:,.2f}")
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    st.write(f"**Grand Total:** ${items_df['total_price'].sum():,.2f}")
                else:
                    st.info("No line items added yet")
                
                st.markdown("---")
                
                # Justification
                if proc['justification']:
                    st.subheader("📝 Justification")
                    st.write(proc['justification'])
                    st.markdown("---")
                
                # Approval Status
                st.subheader("✅ Approval Status")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Level 1 Authorization:**")
                    if proc['level1_approved_at']:
                        st.success(f"✅ Approved by {proc['level1_approver']} on {proc['level1_approved_at']}")
                    elif proc['status'] in ['pending_level1', 'pending_level2', 'approved']:
                        st.info(f"⏳ Pending: {proc['level1_approver'] if proc['level1_approver'] else 'Not assigned'}")
                    else:
                        st.warning("⏸️ Not submitted")
                
                with col2:
                    st.write("**Level 2 Approval:**")
                    if proc['level2_approved_at']:
                        st.success(f"✅ Approved by {proc['level2_approver']} on {proc['level2_approved_at']}")
                    elif proc['status'] == 'pending_level2':
                        st.info(f"⏳ Pending: {proc['level2_approver'] if proc['level2_approver'] else 'Not assigned'}")
                    else:
                        st.warning("⏸️ Awaiting Level 1")
                
                st.markdown("---")
                
                # ========== PHASE 2: ACTION BUTTONS ==========
                st.subheader("⚡ Actions")
                
                # Initialize action states
                if 'show_edit_procurement' not in st.session_state:
                    st.session_state.show_edit_procurement = False
                if 'show_add_items' not in st.session_state:
                    st.session_state.show_add_items = False
                if 'show_add_note' not in st.session_state:
                    st.session_state.show_add_note = False
                
                action_col1, action_col2, action_col3, action_col4, action_col5 = st.columns(5)
                
                # Submit for Approval (Draft only)
                if proc['status'] == 'draft':
                    with action_col1:
                        if st.button("📤 Submit for Approval"):
                            # Assign to first Level 1 approver
                            get_approver = "SELECT TOP 1 approver_id FROM dbo.Procurement_Approvers WHERE approval_level = 1 AND is_active = 1"
                            approver_df, _ = execute_query(get_approver)
                            if approver_df is not None and len(approver_df) > 0:
                                approver_id = approver_df.iloc[0]['approver_id']
                                update_query = """
                                    UPDATE dbo.Procurement_Requests 
                                    SET status = 'pending_level1', level1_approver_id = ?, updated_at = GETDATE()
                                    WHERE request_id = ?
                                """
                                success, error = execute_non_query(update_query, (approver_id, st.session_state.view_procurement_id))
                                if success:
                                    st.success("✅ Submitted for Level 1 approval!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {error}")
                
                # Edit Request (Draft or Rejected only)
                if proc['status'] in ['draft', 'rejected']:
                    with action_col2:
                        if st.button("✏️ Edit Request"):
                            st.session_state.show_edit_procurement = not st.session_state.show_edit_procurement
                            st.rerun()
                
                # Approve (Pending Level 1 or 2)
                if proc['status'] == 'pending_level1':
                    with action_col3:
                        if st.button("✅ Approve (L1)"):
                            # Assign to first Level 2 approver
                            get_approver = "SELECT TOP 1 approver_id FROM dbo.Procurement_Approvers WHERE approval_level = 2 AND is_active = 1"
                            approver_df, _ = execute_query(get_approver)
                            if approver_df is not None and len(approver_df) > 0:
                                approver_id = approver_df.iloc[0]['approver_id']
                                update_query = """
                                    UPDATE dbo.Procurement_Requests 
                                    SET status = 'pending_level2', 
                                        level1_approved_at = GETDATE(),
                                        level2_approver_id = ?,
                                        updated_at = GETDATE()
                                    WHERE request_id = ?
                                """
                                success, error = execute_non_query(update_query, (approver_id, st.session_state.view_procurement_id))
                                if success:
                                    # Add note
                                    note_query = "INSERT INTO dbo.Procurement_Notes (request_id, note_text, note_type, created_by) VALUES (?, 'Level 1 approved', 'approval', 'Admin')"
                                    execute_non_query(note_query, (st.session_state.view_procurement_id,))
                                    st.success("✅ Level 1 Approved! Moving to Level 2...")
                                    st.rerun()
                    
                    with action_col4:
                        if st.button("❌ Reject (L1)"):
                            update_query = """
                                UPDATE dbo.Procurement_Requests 
                                SET status = 'rejected', updated_at = GETDATE()
                                WHERE request_id = ?
                            """
                            success, error = execute_non_query(update_query, (st.session_state.view_procurement_id,))
                            if success:
                                note_query = "INSERT INTO dbo.Procurement_Notes (request_id, note_text, note_type, created_by) VALUES (?, 'Level 1 rejected', 'rejection', 'Admin')"
                                execute_non_query(note_query, (st.session_state.view_procurement_id,))
                                st.warning("❌ Request Rejected")
                                st.rerun()
                
                elif proc['status'] == 'pending_level2':
                    with action_col3:
                        if st.button("✅ Final Approve (L2)"):
                            update_query = """
                                UPDATE dbo.Procurement_Requests 
                                SET status = 'approved', 
                                    level2_approved_at = GETDATE(),
                                    updated_at = GETDATE()
                                WHERE request_id = ?
                            """
                            success, error = execute_non_query(update_query, (st.session_state.view_procurement_id,))
                            if success:
                                note_query = "INSERT INTO dbo.Procurement_Notes (request_id, note_text, note_type, created_by) VALUES (?, 'Level 2 approved - Final approval complete', 'approval', 'Admin')"
                                execute_non_query(note_query, (st.session_state.view_procurement_id,))
                                st.success("✅ Request Fully Approved!")
                                st.rerun()
                    
                    with action_col4:
                        if st.button("❌ Reject (L2)"):
                            update_query = """
                                UPDATE dbo.Procurement_Requests 
                                SET status = 'rejected', updated_at = GETDATE()
                                WHERE request_id = ?
                            """
                            success, error = execute_non_query(update_query, (st.session_state.view_procurement_id,))
                            if success:
                                note_query = "INSERT INTO dbo.Procurement_Notes (request_id, note_text, note_type, created_by) VALUES (?, 'Level 2 rejected', 'rejection', 'Admin')"
                                execute_non_query(note_query, (st.session_state.view_procurement_id,))
                                st.warning("❌ Request Rejected")
                                st.rerun()
                
                # Status Changes (Approved status only)
                if proc['status'] == 'approved':
                    with action_col3:
                        if st.button("📦 Mark as Ordered"):
                            update_query = "UPDATE dbo.Procurement_Requests SET status = 'ordered', updated_at = GETDATE() WHERE request_id = ?"
                            success, _ = execute_non_query(update_query, (st.session_state.view_procurement_id,))
                            if success:
                                note_query = "INSERT INTO dbo.Procurement_Notes (request_id, note_text, note_type, created_by) VALUES (?, 'Order placed with vendor', 'status_change', 'Admin')"
                                execute_non_query(note_query, (st.session_state.view_procurement_id,))
                                st.success("📦 Marked as Ordered")
                                st.rerun()
                
                if proc['status'] == 'ordered':
                    with action_col3:
                        if st.button("✅ Mark as Received"):
                            update_query = "UPDATE dbo.Procurement_Requests SET status = 'received', updated_at = GETDATE() WHERE request_id = ?"
                            success, _ = execute_non_query(update_query, (st.session_state.view_procurement_id,))
                            if success:
                                note_query = "INSERT INTO dbo.Procurement_Notes (request_id, note_text, note_type, created_by) VALUES (?, 'Order received and verified', 'status_change', 'Admin')"
                                execute_non_query(note_query, (st.session_state.view_procurement_id,))
                                st.success("✅ Marked as Received")
                                st.rerun()
                
                # Add Line Items (Draft only)
                if proc['status'] == 'draft':
                    with action_col5:
                        if st.button("➕ Add Items"):
                            st.session_state.show_add_items = not st.session_state.show_add_items
                            st.rerun()
                
                # Add Note (Always available)
                with action_col5 if proc['status'] != 'draft' else action_col4:
                    if st.button("💬 Add Note"):
                        st.session_state.show_add_note = not st.session_state.show_add_note
                        st.rerun()
                
                st.markdown("---")
                
                # ========== EDIT REQUEST FORM ==========
                if st.session_state.show_edit_procurement:
                    with st.expander("✏️ Edit Request", expanded=True):
                        with st.form("edit_procurement_form"):
                            st.markdown("### Request Information")
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                edit_name = st.text_input("Requester Name*", value=proc['requester_name'])
                                edit_email = st.text_input("Email*", value=proc['requester_email'])
                                edit_phone = st.text_input("Phone", value=proc['requester_phone'] if proc['requester_phone'] else "")
                            
                            with col2:
                                locations = ["Crater", "Dinwiddie County", "Greensville/Emporia", "Surry County", "Prince George", "Sussex County", "Hopewell"]
                                edit_location = st.selectbox("Location*", locations, index=locations.index(proc['location']) if proc['location'] in locations else 0)
                                edit_department = st.text_input("Department", value=proc['department'] if proc['department'] else "")
                                priorities = ["low", "normal", "high", "urgent"]
                                edit_priority = st.selectbox("Priority*", priorities, index=priorities.index(proc['priority']) if proc['priority'] in priorities else 1)
                            
                            with col3:
                                edit_delivery = st.date_input("Delivery Required By", value=proc['delivery_required_by'] if proc['delivery_required_by'] else None)
                                
                                cst_query = "SELECT DISTINCT code_value FROM dbo.Procurement_Codes WHERE code_type = 'CST' ORDER BY code_value"
                                cst_df, _ = execute_query(cst_query)
                                cst_options = [""] + (cst_df['code_value'].tolist() if cst_df is not None else [])
                                edit_cst = st.selectbox("CST Code", cst_options, index=cst_options.index(proc['cst_code']) if proc['cst_code'] in cst_options else 0)
                                
                                coa_query = "SELECT DISTINCT code_value FROM dbo.Procurement_Codes WHERE code_type = 'COA' ORDER BY code_value"
                                coa_df, _ = execute_query(coa_query)
                                coa_options = [""] + (coa_df['code_value'].tolist() if coa_df is not None else [])
                                edit_coa = st.selectbox("COA Code", coa_options, index=coa_options.index(proc['coa_code']) if proc['coa_code'] in coa_options else 0)
                            
                            st.markdown("### Vendor Information")
                            col1, col2 = st.columns(2)
                            with col1:
                                edit_vendor = st.text_input("Vendor Name*", value=proc['vendor_name'])
                                edit_vendor_contact = st.text_input("Contact Person", value=proc['vendor_contact'] if proc['vendor_contact'] else "")
                            with col2:
                                edit_vendor_phone = st.text_input("Vendor Phone", value=proc['vendor_phone'] if proc['vendor_phone'] else "")
                                edit_vendor_email = st.text_input("Vendor Email", value=proc['vendor_email'] if proc['vendor_email'] else "")
                            
                            edit_justification = st.text_area("Justification*", value=proc['justification'], height=100)
                            
                            col1, col2 = st.columns([1, 5])
                            with col1:
                                save_edit = st.form_submit_button("Save Changes")
                            with col2:
                                cancel_edit = st.form_submit_button("Cancel")
                            
                            if save_edit:
                                if edit_name and edit_email and edit_location and edit_vendor and edit_justification:
                                    update_query = """
                                        UPDATE dbo.Procurement_Requests 
                                        SET requester_name=?, requester_email=?, requester_phone=?, location=?, department=?,
                                            priority=?, delivery_required_by=?, cst_code=?, coa_code=?,
                                            vendor_name=?, vendor_contact=?, vendor_phone=?, vendor_email=?,
                                            justification=?, updated_at=GETDATE()
                                        WHERE request_id=?
                                    """
                                    success, error = execute_non_query(update_query, (
                                        edit_name, edit_email, edit_phone or None, edit_location, edit_department or None,
                                        edit_priority, edit_delivery, edit_cst or None, edit_coa or None,
                                        edit_vendor, edit_vendor_contact or None, edit_vendor_phone or None, edit_vendor_email or None,
                                        edit_justification, st.session_state.view_procurement_id
                                    ))
                                    if success:
                                        st.success("✅ Request updated successfully!")
                                        st.session_state.show_edit_procurement = False
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {error}")
                                else:
                                    st.error("Please fill in all required fields (*)")
                            
                            if cancel_edit:
                                st.session_state.show_edit_procurement = False
                                st.rerun()
                
                # ========== ADD LINE ITEMS FORM ==========
                if st.session_state.show_add_items:
                    with st.expander("➕ Add Line Items", expanded=True):
                        with st.form("add_items_form"):
                            st.markdown("### New Line Item")
                            
                            item_desc = st.text_input("Item Description*")
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                item_qty = st.number_input("Quantity*", min_value=1, value=1)
                            with col2:
                                item_price = st.number_input("Unit Price*", min_value=0.01, value=1.00, step=0.01)
                            with col3:
                                item_total = item_qty * item_price
                                st.metric("Total", f"${item_total:,.2f}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                item_manufacturer = st.text_input("Manufacturer")
                            with col2:
                                item_model = st.text_input("Model/Part Number")
                            
                            item_notes = st.text_area("Notes", height=60)
                            
                            col1, col2 = st.columns([1, 5])
                            with col1:
                                add_item = st.form_submit_button("Add Item")
                            with col2:
                                cancel_item = st.form_submit_button("Cancel")
                            
                            if add_item:
                                if item_desc:
                                    # Get next line number
                                    line_query = f"SELECT ISNULL(MAX(line_number), 0) + 1 as next_line FROM dbo.Procurement_Items WHERE request_id = {st.session_state.view_procurement_id}"
                                    line_df, _ = execute_query(line_query)
                                    next_line = line_df.iloc[0]['next_line'] if line_df is not None else 1
                                    
                                    insert_query = """
                                        INSERT INTO dbo.Procurement_Items (
                                            request_id, line_number, item_description, quantity, unit_price,
                                            manufacturer, model_number, notes
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    """
                                    success, error = execute_non_query(insert_query, (
                                        st.session_state.view_procurement_id, next_line, item_desc, item_qty, item_price,
                                        item_manufacturer or None, item_model or None, item_notes or None
                                    ))
                                    if success:
                                        # Update total amount
                                        update_total = """
                                            UPDATE dbo.Procurement_Requests 
                                            SET total_amount = (SELECT SUM(quantity * unit_price) FROM dbo.Procurement_Items WHERE request_id = ?)
                                            WHERE request_id = ?
                                        """
                                        execute_non_query(update_total, (st.session_state.view_procurement_id, st.session_state.view_procurement_id))
                                        
                                        st.success("✅ Item added successfully!")
                                        st.session_state.show_add_items = False
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {error}")
                                else:
                                    st.error("Please enter item description")
                            
                            if cancel_item:
                                st.session_state.show_add_items = False
                                st.rerun()
                
                # ========== ADD NOTE FORM ==========
                if st.session_state.show_add_note:
                    with st.expander("💬 Add Note", expanded=True):
                        with st.form("add_note_form"):
                            note_text = st.text_area("Note/Comment", height=100)
                            
                            col1, col2 = st.columns([1, 5])
                            with col1:
                                add_note_btn = st.form_submit_button("Add Note")
                            with col2:
                                cancel_note = st.form_submit_button("Cancel")
                            
                            if add_note_btn:
                                if note_text:
                                    insert_note = "INSERT INTO dbo.Procurement_Notes (request_id, note_text, note_type, created_by) VALUES (?, ?, 'comment', 'Admin')"
                                    success, error = execute_non_query(insert_note, (st.session_state.view_procurement_id, note_text))
                                    if success:
                                        st.success("✅ Note added!")
                                        st.session_state.show_add_note = False
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {error}")
                                else:
                                    st.error("Please enter note text")
                            
                            if cancel_note:
                                st.session_state.show_add_note = False
                                st.rerun()
                
                # ========== DISPLAY NOTES/HISTORY ==========
                st.markdown("---")
                st.subheader("💬 Notes & History")
                
                notes_query = f"""
                    SELECT note_text, note_type, created_by, created_at 
                    FROM dbo.Procurement_Notes 
                    WHERE request_id = {st.session_state.view_procurement_id}
                    ORDER BY created_at DESC
                """
                notes_df, error = execute_query(notes_query)
                
                if not error and notes_df is not None and len(notes_df) > 0:
                    for _, note in notes_df.iterrows():
                        note_icon = {
                            'comment': '💬',
                            'approval': '✅',
                            'rejection': '❌',
                            'status_change': '🔄'
                        }.get(note['note_type'], '📝')
                        
                        st.markdown(f"""
                        <div class="note-card">
                            {note_icon} <small><strong>{note['created_by']}</strong> - {note['created_at']}</small><br>
                            {note['note_text']}
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No notes or history yet")
        
        else:
            # List View
            
            # Top actions
            col1, col2 = st.columns([6, 1])
            with col2:
                if st.button("➕ New Request"):
                    st.session_state.show_create_procurement = not st.session_state.show_create_procurement
            
            # Create New Request Form
            if st.session_state.show_create_procurement:
                with st.expander("📝 Create Procurement Request", expanded=True):
                    with st.form("new_procurement_form"):
                        st.markdown("### Request Information")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            requester_name = st.text_input("Requester Name*")
                            requester_email = st.text_input("Email*")
                            requester_phone = st.text_input("Phone")
                        
                        with col2:
                            location = st.selectbox("Location*", [
                                "Crater", "Dinwiddie County", "Greensville/Emporia",
                                "Surry County", "Prince George", "Sussex County", "Hopewell"
                            ])
                            department = st.text_input("Department")
                            priority = st.selectbox("Priority*", ["normal", "low", "high", "urgent"])
                        
                        with col3:
                            delivery_date = st.date_input("Delivery Required By")
                            
                            # Get coding options
                            cst_query = "SELECT DISTINCT code_value FROM dbo.Procurement_Codes WHERE code_type = 'CST' ORDER BY code_value"
                            cst_df, _ = execute_query(cst_query)
                            cst_options = [""] + (cst_df['code_value'].tolist() if cst_df is not None else [])
                            cst_code = st.selectbox("CST Code", cst_options)
                            
                            coa_query = "SELECT DISTINCT code_value FROM dbo.Procurement_Codes WHERE code_type = 'COA' ORDER BY code_value"
                            coa_df, _ = execute_query(coa_query)
                            coa_options = [""] + (coa_df['code_value'].tolist() if coa_df is not None else [])
                            coa_code = st.selectbox("COA Code", coa_options)
                        
                        st.markdown("### Vendor Information")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            vendor_name = st.text_input("Vendor Name*")
                            vendor_contact = st.text_input("Contact Person")
                        
                        with col2:
                            vendor_phone = st.text_input("Vendor Phone")
                            vendor_email = st.text_input("Vendor Email")
                        
                        st.markdown("### Line Items")
                        st.info("💡 You can add items after creating the request")
                        
                        item_desc = st.text_input("Item Description*")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            quantity = st.number_input("Quantity*", min_value=1, value=1)
                        with col2:
                            unit_price = st.number_input("Unit Price*", min_value=0.01, value=1.00, step=0.01)
                        with col3:
                            total = quantity * unit_price
                            st.metric("Line Total", f"${total:,.2f}")
                        
                        justification = st.text_area("Justification*", height=100)
                        
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            submit = st.form_submit_button("Create Request")
                        with col2:
                            cancel = st.form_submit_button("Cancel")
                        
                        if submit:
                            if requester_name and requester_email and location and vendor_name and item_desc and justification:
                                # Generate request number
                                gen_num_query = "DECLARE @num VARCHAR(50); EXEC dbo.sp_GenerateProcurementRequestNumber @num OUTPUT; SELECT @num as request_number"
                                num_result, num_error = execute_query(gen_num_query)
                                
                                if num_error or num_result is None:
                                    st.error("Error generating request number. Please ensure stored procedure exists.")
                                else:
                                    request_number = num_result.iloc[0]['request_number']
                                    
                                    # Insert request
                                    insert_query = """
                                        INSERT INTO dbo.Procurement_Requests (
                                            request_number, request_date, requester_name, requester_email, requester_phone,
                                            location, department, cst_code, coa_code, vendor_name, vendor_contact,
                                            vendor_phone, vendor_email, total_amount, justification, status, priority,
                                            delivery_required_by, created_by
                                        ) OUTPUT INSERTED.request_id
                                        VALUES (?, GETDATE(), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?, 'System')
                                    """
                                    
                                    success, error = execute_non_query(
                                        insert_query,
                                        (request_number, requester_name, requester_email, requester_phone or None,
                                         location, department or None, cst_code or None, coa_code or None,
                                         vendor_name, vendor_contact or None, vendor_phone or None, vendor_email or None,
                                         total, justification, priority, delivery_date)
                                    )
                                    
                                    if success:
                                        # Get the request_id
                                        get_id_query = f"SELECT request_id FROM dbo.Procurement_Requests WHERE request_number = '{request_number}'"
                                        id_result, _ = execute_query(get_id_query)
                                        
                                        if id_result is not None and len(id_result) > 0:
                                            request_id = id_result.iloc[0]['request_id']
                                            
                                            # Insert line item
                                            item_query = """
                                                INSERT INTO dbo.Procurement_Items (
                                                    request_id, line_number, item_description, quantity, unit_price
                                                ) VALUES (?, 1, ?, ?, ?)
                                            """
                                            execute_non_query(item_query, (request_id, item_desc, quantity, unit_price))
                                        
                                        st.success(f"✅ Procurement request {request_number} created successfully!")
                                        st.session_state.show_create_procurement = False
                                        st.rerun()
                                    else:
                                        st.error(f"Error creating request: {error}")
                            else:
                                st.error("Please fill in all required fields (*)")
                        
                        if cancel:
                            st.session_state.show_create_procurement = False
                            st.rerun()
            
            st.markdown("---")
            
            # Filters
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                status_filter = st.selectbox("Status", ["All", "draft", "pending_level1", "pending_level2", "approved", "rejected", "ordered", "received"])
            with col2:
                priority_filter = st.selectbox("Priority", ["All", "low", "normal", "high", "urgent"])
            with col3:
                location_filter = st.selectbox("Location", ["All", "Crater", "Dinwiddie County", "Greensville/Emporia", "Surry County", "Prince George", "Sussex County", "Hopewell"])
            with col4:
                search = st.text_input("🔍 Search", placeholder="Search requests...")
            
            # Build query
            query = """
                SELECT request_id, request_number, request_date, requester_name, vendor_name, 
                       total_amount, status, priority, location, created_at
                FROM dbo.Procurement_Requests WHERE 1=1
            """
            
            if status_filter != "All":
                query += f" AND status = '{status_filter}'"
            if priority_filter != "All":
                query += f" AND priority = '{priority_filter}'"
            if location_filter != "All":
                query += f" AND location = '{location_filter}'"
            if search:
                query += f" AND (request_number LIKE '%{search}%' OR requester_name LIKE '%{search}%' OR vendor_name LIKE '%{search}%')"
            
            query += " ORDER BY request_date DESC"
            
            df, error = execute_query(query)
            
            if error:
                st.error(f"Error: {error}")
            elif df is None or len(df) == 0:
                st.info("No procurement requests found")
            else:
                st.write(f"**Total:** {len(df)} requests")
                
                # Display requests
                for idx, row in df.iterrows():
                    col1, col2 = st.columns([9, 1])
                    with col1:
                        status_colors = {
                            'draft': '⚪', 'pending_level1': '🟠', 'pending_level2': '🔵',
                            'approved': '🟢', 'rejected': '🔴', 'ordered': '🔵',
                            'received': '🟢', 'cancelled': '⚫'
                        }
                        priority_colors = {'low': '🟢', 'normal': '⚪', 'high': '🟠', 'urgent': '🔴'}
                        
                        st.markdown(f"""
                        <div class="ticket-card">
                            {status_colors.get(row['status'], '⚪')} {priority_colors.get(row['priority'], '⚪')} 
                            <strong>{row['request_number']}</strong> - {row['vendor_name']}<br>
                            <small>Requester: {row['requester_name']} | Amount: ${row['total_amount']:,.2f} | Location: {row['location']} | Date: {row['request_date']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        if st.button("View", key=f"view_proc_{row['request_id']}"):
                            st.session_state.view_procurement_id = row['request_id']
                            st.rerun()

elif page == "📈 Reports":
    st.header("📈 Advanced Reporting")
    
    st.markdown("""
    Generate comprehensive reports with custom date ranges and export to multiple formats.
    """)
    
    # Report Configuration
    with st.expander("⚙️ Report Configuration", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            report_type = st.selectbox("Report Type", [
                "Ticket Summary",
                "Detailed Ticket Report",
                "Ticket Performance Metrics",
                "Tickets by Location",
                "Tickets by Priority",
                "Asset Summary",
                "Asset Deployment Report",
                "Asset Warranty Report"
            ])
        
        with col2:
            date_from = st.date_input("From Date", value=datetime.now() - timedelta(days=30))
        
        with col3:
            date_to = st.date_input("To Date", value=datetime.now())
    
    # Generate Report Button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("📊 Generate Preview", use_container_width=True):
            with st.spinner("Generating report..."):
                # Build query based on report type
                if report_type == "Ticket Summary":
                    query = f"""
                        SELECT 
                            status,
                            priority,
                            COUNT(*) as ticket_count,
                            location
                        FROM dbo.Tickets
                        WHERE created_at >= '{date_from}' AND created_at <= '{date_to}'
                        GROUP BY status, priority, location
                        ORDER BY status, priority
                    """
                    report_title = f"Ticket Summary Report ({date_from} to {date_to})"
                
                elif report_type == "Detailed Ticket Report":
                    query = f"""
                        SELECT 
                            ticket_id,
                            short_description as subject,
                            name as customer,
                            email,
                            status,
                            priority,
                            location,
                            assigned_to,
                            created_at,
                            first_response_at,
                            resolved_at
                        FROM dbo.Tickets
                        WHERE created_at >= '{date_from}' AND created_at <= '{date_to}'
                        ORDER BY created_at DESC
                    """
                    report_title = f"Detailed Ticket Report ({date_from} to {date_to})"
                
                elif report_type == "Ticket Performance Metrics":
                    query = f"""
                        SELECT 
                            location,
                            COUNT(*) as total_tickets,
                            SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_tickets,
                            AVG(CASE WHEN first_response_at IS NOT NULL 
                                THEN DATEDIFF(hour, created_at, first_response_at) 
                                ELSE NULL END) as avg_response_hours,
                            AVG(CASE WHEN resolved_at IS NOT NULL 
                                THEN DATEDIFF(hour, created_at, resolved_at) 
                                ELSE NULL END) as avg_resolution_hours
                        FROM dbo.Tickets
                        WHERE created_at >= '{date_from}' AND created_at <= '{date_to}'
                        GROUP BY location
                        ORDER BY total_tickets DESC
                    """
                    report_title = f"Ticket Performance Metrics ({date_from} to {date_to})"
                
                elif report_type == "Tickets by Location":
                    query = f"""
                        SELECT 
                            location,
                            status,
                            priority,
                            COUNT(*) as ticket_count
                        FROM dbo.Tickets
                        WHERE created_at >= '{date_from}' AND created_at <= '{date_to}'
                        GROUP BY location, status, priority
                        ORDER BY location, status
                    """
                    report_title = f"Tickets by Location Report ({date_from} to {date_to})"
                
                elif report_type == "Tickets by Priority":
                    query = f"""
                        SELECT 
                            priority,
                            status,
                            COUNT(*) as ticket_count,
                            AVG(CASE WHEN resolved_at IS NOT NULL 
                                THEN DATEDIFF(hour, created_at, resolved_at) 
                                ELSE NULL END) as avg_resolution_hours
                        FROM dbo.Tickets
                        WHERE created_at >= '{date_from}' AND created_at <= '{date_to}'
                        GROUP BY priority, status
                        ORDER BY CASE priority 
                            WHEN 'urgent' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            WHEN 'low' THEN 4 END
                    """
                    report_title = f"Tickets by Priority Report ({date_from} to {date_to})"
                
                elif report_type == "Asset Summary":
                    query = """
                        SELECT 
                            type,
                            status,
                            COUNT(*) as asset_count,
                            location
                        FROM dbo.Assets
                        GROUP BY type, status, location
                        ORDER BY type, status
                    """
                    report_title = "Asset Summary Report"
                
                elif report_type == "Asset Deployment Report":
                    query = """
                        SELECT 
                            asset_tag,
                            type,
                            model,
                            serial,
                            status,
                            location,
                            assigned_user,
                            assigned_email,
                            purchase_date
                        FROM dbo.Assets
                        WHERE status = 'Deployed'
                        ORDER BY location, type
                    """
                    report_title = "Asset Deployment Report"
                
                elif report_type == "Asset Warranty Report":
                    query = """
                        SELECT 
                            asset_tag,
                            type,
                            model,
                            serial,
                            location,
                            assigned_user,
                            purchase_date,
                            warranty_expiration,
                            DATEDIFF(day, GETDATE(), warranty_expiration) as days_until_expiry
                        FROM dbo.Assets
                        WHERE warranty_expiration IS NOT NULL
                        ORDER BY warranty_expiration
                    """
                    report_title = "Asset Warranty Report"
                
                # Execute query
                df, error = execute_query(query)
                
                if error:
                    st.error(f"Error generating report: {error}")
                else:
                    st.session_state.report_preview_data = {
                        'df': df,
                        'title': report_title,
                        'type': report_type
                    }
                    st.success(f"✅ Report generated! {len(df)} rows")
    
    with col2:
        if st.button("🔄 Clear Preview", use_container_width=True):
            st.session_state.report_preview_data = None
            st.rerun()
    
    # Display Preview
    if st.session_state.report_preview_data:
        st.markdown("---")
        st.subheader("👁️ Report Preview")
        st.write(f"**{st.session_state.report_preview_data['title']}**")
        st.write(f"Total Records: **{len(st.session_state.report_preview_data['df'])}**")
        
        st.dataframe(st.session_state.report_preview_data['df'], use_container_width=True, height=400)
        
        # Export Options
        st.markdown("---")
        st.subheader("💾 Export Report")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Excel Export
            if HAS_EXCEL:
                excel_file, excel_error = generate_excel_report(
                    st.session_state.report_preview_data['df'],
                    st.session_state.report_preview_data['title']
                )
                
                if excel_file and not excel_error:
                    st.download_button(
                        label="📗 Download Excel",
                        data=excel_file,
                        file_name=f"{st.session_state.report_preview_data['type'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.error(f"Excel export error: {excel_error}")
            else:
                st.info("📗 Excel export requires openpyxl")
        
        with col2:
            # PDF Export
            if HAS_PDF:
                pdf_file, pdf_error = generate_pdf_report(
                    st.session_state.report_preview_data['df'],
                    st.session_state.report_preview_data['title']
                )
                
                if pdf_file and not pdf_error:
                    st.download_button(
                        label="📕 Download PDF",
                        data=pdf_file,
                        file_name=f"{st.session_state.report_preview_data['type'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.error(f"PDF export error: {pdf_error}")
            else:
                st.info("📕 PDF export requires reportlab")
        
        with col3:
            # CSV Export
            csv_file, csv_error = generate_csv_report(st.session_state.report_preview_data['df'])
            
            if csv_file and not csv_error:
                st.download_button(
                    label="📄 Download CSV",
                    data=csv_file,
                    file_name=f"{st.session_state.report_preview_data['type'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.error(f"CSV export error: {csv_error}")

elif page == "🎫 Tickets":
    st.header("🎫 Ticket Management")
    
    # Back button if viewing ticket details
    if st.session_state.view_ticket_id:
        if st.button("← Back to Ticket List"):
            st.session_state.view_ticket_id = None
            st.session_state.edit_ticket_id = None
            st.rerun()
        
        st.markdown("---")
        
        # Load ticket details
        ticket_query = f"""
            SELECT * FROM dbo.Tickets 
            WHERE ticket_id = {st.session_state.view_ticket_id}
        """
        ticket_df, error = execute_query(ticket_query)
        
        if error or ticket_df is None or len(ticket_df) == 0:
            st.error("Ticket not found")
            st.session_state.view_ticket_id = None
        else:
            ticket = ticket_df.iloc[0]
            
            # Ticket Header
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.subheader(f"Ticket #{ticket['ticket_id']}: {ticket['short_description']}")
            with col2:
                priority_colors = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'urgent': '🔴'}
                st.write(f"{priority_colors.get(ticket['priority'], '⚪')} Priority: **{ticket['priority'].upper()}**")
            with col3:
                if st.button("✏️ Edit Ticket"):
                    st.session_state.edit_ticket_id = st.session_state.view_ticket_id
                    st.rerun()
            
            st.markdown("---")
            
            # Show Edit Form if editing
            if st.session_state.edit_ticket_id == st.session_state.view_ticket_id:
                with st.expander("✏️ Edit Ticket", expanded=True):
                    with st.form("edit_ticket_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            status = st.selectbox("Status*", 
                                ["open", "in_progress", "on_hold", "waiting_customer_response", "resolved", "closed"],
                                index=["open", "in_progress", "on_hold", "waiting_customer_response", "resolved", "closed"].index(ticket['status'])
                            )
                            priority = st.selectbox("Priority*", 
                                ["low", "medium", "high", "urgent"],
                                index=["low", "medium", "high", "urgent"].index(ticket['priority'])
                            )
                            # Get list of users for assignment
                            users_query = "SELECT id, CONCAT(first_name, ' ', last_name) as name FROM dbo.users WHERE role IN ('admin', 'technician') ORDER BY name"
                            users_df, users_error = execute_query(users_query)
                            
                            if not users_error and users_df is not None:
                                user_options = ["Unassigned"] + users_df['name'].tolist()
                                current_assigned = ticket['assigned_to'] if ticket['assigned_to'] else "Unassigned"
                                assigned_to = st.selectbox("Assign To", user_options, 
                                    index=user_options.index(current_assigned) if current_assigned in user_options else 0
                                )
                        
                        with col2:
                            short_desc = st.text_input("Subject*", value=ticket['short_description'])
                            location = st.selectbox("Location*", [
                                "Crater", "Dinwiddie County", "Greensville/Emporia",
                                "Surry County", "Prince George", "Sussex County", "Hopewell"
                            ], index=["Crater", "Dinwiddie County", "Greensville/Emporia", "Surry County", "Prince George", "Sussex County", "Hopewell"].index(ticket['location']) if ticket['location'] in ["Crater", "Dinwiddie County", "Greensville/Emporia", "Surry County", "Prince George", "Sussex County", "Hopewell"] else 0)
                        
                        description = st.text_area("Description*", value=ticket['description'], height=100)
                        
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            submit = st.form_submit_button("Save Changes")
                        with col2:
                            cancel = st.form_submit_button("Cancel")
                        
                        if submit:
                            # Build UPDATE query
                            update_parts = []
                            params_list = []
                            
                            # Check what changed and update accordingly
                            if status != ticket['status']:
                                update_parts.append("status = ?")
                                params_list.append(status)
                                
                                # Set first_response_at if moving from open to in_progress
                                if ticket['status'] == 'open' and status == 'in_progress' and not ticket['first_response_at']:
                                    update_parts.append("first_response_at = GETDATE()")
                                
                                # Set resolved_at if moving to resolved
                                if status == 'resolved' and not ticket['resolved_at']:
                                    update_parts.append("resolved_at = GETDATE()")
                            
                            if priority != ticket['priority']:
                                update_parts.append("priority = ?")
                                params_list.append(priority)
                            
                            assigned_value = None if assigned_to == "Unassigned" else assigned_to
                            if assigned_value != ticket['assigned_to']:
                                update_parts.append("assigned_to = ?")
                                params_list.append(assigned_value)
                            
                            if short_desc != ticket['short_description']:
                                update_parts.append("short_description = ?")
                                params_list.append(short_desc)
                            
                            if description != ticket['description']:
                                update_parts.append("description = ?")
                                params_list.append(description)
                            
                            if location != ticket['location']:
                                update_parts.append("location = ?")
                                params_list.append(location)
                            
                            if update_parts:
                                query = f"UPDATE dbo.Tickets SET {', '.join(update_parts)} WHERE ticket_id = ?"
                                params_list.append(st.session_state.view_ticket_id)
                                
                                success, error = execute_non_query(query, tuple(params_list))
                                
                                if success:
                                    st.success("✅ Ticket updated successfully!")
                                    st.session_state.edit_ticket_id = None
                                    st.rerun()
                                else:
                                    st.error(f"Error: {error}")
                            else:
                                st.info("No changes detected")
                        
                        if cancel:
                            st.session_state.edit_ticket_id = None
                            st.rerun()
            
            # Ticket Details
            st.subheader("📋 Ticket Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Customer:** {ticket['name']}")
                st.write(f"**Email:** {ticket['email']}")
                if ticket['phone_number']:
                    st.write(f"**Phone:** {ticket['phone_number']}")
                st.write(f"**Location:** {ticket['location']}")
            
            with col2:
                st.write(f"**Status:** {ticket['status']}")
                st.write(f"**Priority:** {ticket['priority']}")
                st.write(f"**Assigned To:** {ticket['assigned_to'] if ticket['assigned_to'] else 'Unassigned'}")
                st.write(f"**Created:** {ticket['created_at']}")
                if ticket['first_response_at']:
                    st.write(f"**First Response:** {ticket['first_response_at']}")
                if ticket['resolved_at']:
                    st.write(f"**Resolved:** {ticket['resolved_at']}")
            
            st.markdown("---")
            st.subheader("📝 Description")
            st.write(ticket['description'])
            
            st.markdown("---")
            
            # Notes/Comments Section
            st.subheader("💬 Notes & Comments")
            
            # Add note form
            with st.form("add_note_form"):
                note_text = st.text_area("Add a note or comment", height=100)
                submit_note = st.form_submit_button("Add Note")
                
                if submit_note and note_text:
                    # First check if table exists
                    check_table = """
                        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ticket_notes')
                        BEGIN
                            CREATE TABLE dbo.ticket_notes (
                                note_id INT IDENTITY(1,1) PRIMARY KEY,
                                ticket_id INT NOT NULL,
                                note_text NVARCHAR(MAX) NOT NULL,
                                created_by NVARCHAR(100) NOT NULL,
                                created_at DATETIME DEFAULT GETDATE(),
                                FOREIGN KEY (ticket_id) REFERENCES dbo.Tickets(ticket_id)
                            );
                        END
                    """
                    execute_non_query(check_table)
                    
                    # Insert note
                    insert_note = """
                        INSERT INTO dbo.ticket_notes (ticket_id, note_text, created_by, created_at)
                        VALUES (?, ?, 'Admin', GETDATE())
                    """
                    success, error = execute_non_query(insert_note, (st.session_state.view_ticket_id, note_text))
                    
                    if success:
                        st.success("✅ Note added!")
                        st.rerun()
                    else:
                        st.error(f"Error: {error}")
            
            # Display existing notes
            notes_df, notes_error = execute_query(
                "SELECT note_id, note_text, created_by, created_at FROM dbo.ticket_notes WHERE ticket_id = ? ORDER BY created_at DESC",
                (st.session_state.view_ticket_id,)
            )
            
            if not notes_error and notes_df is not None and len(notes_df) > 0:
                st.markdown("### Previous Notes:")
                for _, note in notes_df.iterrows():
                    st.markdown(f"""
                    <div class="note-card">
                        <small><strong>{note['created_by']}</strong> - {note['created_at']}</small><br>
                        {note['note_text']}
                    </div>
                    """, unsafe_allow_html=True)
    
    else:
        # Ticket List View
        # Add New Ticket Button
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("➕ New Ticket"):
                st.session_state.show_add_ticket_form = not st.session_state.show_add_ticket_form
        
        # Show Add Ticket Form
        if st.session_state.show_add_ticket_form:
            with st.expander("📝 Create New Ticket", expanded=True):
                with st.form("new_ticket_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        name = st.text_input("Customer Name*")
                        email = st.text_input("Email*")
                        phone = st.text_input("Phone Number")
                        location = st.selectbox("Location*", [
                            "Crater", "Dinwiddie County", "Greensville/Emporia",
                            "Surry County", "Prince George", "Sussex County", "Hopewell"
                        ])
                    
                    with col2:
                        priority = st.selectbox("Priority*", ["low", "medium", "high", "urgent"])
                        status = st.selectbox("Status*", ["open", "in_progress", "on_hold", "waiting_customer_response", "resolved", "closed"])
                        short_description = st.text_input("Subject*")
                    
                    description = st.text_area("Description*", height=100)
                    
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        submit = st.form_submit_button("Submit Ticket")
                    with col2:
                        cancel = st.form_submit_button("Cancel")
                    
                    if submit:
                        if name and email and location and short_description and description:
                            query = """
                                INSERT INTO dbo.Tickets 
                                (name, email, phone_number, location, priority, status, short_description, description, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                            """
                            success, error = execute_non_query(query, (name, email, phone, location, priority, status, short_description, description))
                            
                            if success:
                                st.success("✅ Ticket created successfully!")
                                st.session_state.show_add_ticket_form = False
                                st.rerun()
                            else:
                                st.error(f"Error: {error}")
                        else:
                            st.error("Please fill in all required fields (*)")
                    
                    if cancel:
                        st.session_state.show_add_ticket_form = False
                        st.rerun()
        
        st.markdown("---")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Status", ["All", "open", "in_progress", "on_hold", "waiting_customer_response", "resolved", "closed"])
        with col2:
            priority_filter = st.selectbox("Priority", ["All", "low", "medium", "high", "urgent"])
        with col3:
            search = st.text_input("🔍 Search", placeholder="Search tickets...")
        
        # Build query
        query = "SELECT ticket_id, short_description, name, email, status, priority, location, assigned_to, created_at FROM dbo.Tickets WHERE 1=1"
        
        if status_filter != "All":
            query += f" AND status = '{status_filter}'"
        if priority_filter != "All":
            query += f" AND priority = '{priority_filter}'"
        if search:
            query += f" AND (short_description LIKE '%{search}%' OR name LIKE '%{search}%' OR email LIKE '%{search}%')"
        
        query += " ORDER BY created_at DESC"
        
        df, error = execute_query(query)
        
        if error:
            st.error(f"Error: {error}")
        else:
            st.write(f"**Total:** {len(df)} tickets")
            
            # Display tickets with view button
            if len(df) > 0:
                for idx, row in df.iterrows():
                    col1, col2 = st.columns([9, 1])
                    with col1:
                        priority_colors = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'urgent': '🔴'}
                        st.markdown(f"""
                        <div class="ticket-card">
                            {priority_colors.get(row['priority'], '⚪')} <strong>#{row['ticket_id']}</strong> - {row['short_description']}<br>
                            <small>Customer: {row['name']} | Status: {row['status']} | Assigned: {row['assigned_to'] if row['assigned_to'] else 'Unassigned'} | Created: {row['created_at']}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        if st.button("View", key=f"view_{row['ticket_id']}"):
                            st.session_state.view_ticket_id = row['ticket_id']
                            st.rerun()

elif page == "💻 Assets":
    st.header("💻 Asset Management")
    
    # Add New Asset Button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("➕ New Asset"):
            st.session_state.show_add_asset_form = not st.session_state.show_add_asset_form
            st.session_state.edit_asset_id = None
    
    # Show Add/Edit Asset Form
    if st.session_state.show_add_asset_form or st.session_state.edit_asset_id:
        
        # If editing, load existing data
        edit_data = None
        if st.session_state.edit_asset_id:
            edit_query = f"SELECT * FROM dbo.Assets WHERE asset_id = {st.session_state.edit_asset_id}"
            edit_df, edit_error = execute_query(edit_query)
            if not edit_error and len(edit_df) > 0:
                edit_data = edit_df.iloc[0]
        
        form_title = "✏️ Edit Asset" if edit_data is not None else "📝 Create New Asset"
        
        with st.expander(form_title, expanded=True):
            with st.form("asset_form"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    asset_tag = st.text_input("Asset Tag*", value=edit_data['asset_tag'] if edit_data is not None else "")
                    asset_type = st.selectbox("Type*", 
                        ["Laptop", "Desktop", "Monitor", "Printer", "Scanner", "Tablet", "Phone", "Server", "Network Equipment", "Other"],
                        index=["Laptop", "Desktop", "Monitor", "Printer", "Scanner", "Tablet", "Phone", "Server", "Network Equipment", "Other"].index(edit_data['type']) if edit_data is not None and edit_data['type'] in ["Laptop", "Desktop", "Monitor", "Printer", "Scanner", "Tablet", "Phone", "Server", "Network Equipment", "Other"] else 0
                    )
                    category = st.text_input("Category*", value=edit_data['category'] if edit_data is not None else "")
                
                with col2:
                    model = st.text_input("Model*", value=edit_data['model'] if edit_data is not None else "")
                    serial_number = st.text_input("Serial Number*", value=edit_data['serial'] if edit_data is not None else "")
                    status = st.selectbox("Status*", 
                        ["Deployed", "In-Stock", "Surplus", "Unaccounted", "Repair", "Retired"],
                        index=["Deployed", "In-Stock", "Surplus", "Unaccounted", "Repair", "Retired"].index(edit_data['status']) if edit_data is not None else 1
                    )
                    location = st.selectbox("Location*", [
                        "Crater", "Dinwiddie County", "Greensville/Emporia", "Surry County", 
                        "Prince George", "Sussex County", "Hopewell", "Central IT"
                    ], index=["Crater", "Dinwiddie County", "Greensville/Emporia", "Surry County", "Prince George", "Sussex County", "Hopewell", "Central IT"].index(edit_data['location']) if edit_data is not None and edit_data['location'] in ["Crater", "Dinwiddie County", "Greensville/Emporia", "Surry County", "Prince George", "Sussex County", "Hopewell", "Central IT"] else 0)
                
                with col3:
                    assigned_user = st.text_input("Assigned User", value=edit_data['assigned_user'] if edit_data is not None and edit_data['assigned_user'] else "")
                    assigned_email = st.text_input("Assigned Email", value=edit_data['assigned_email'] if edit_data is not None and edit_data['assigned_email'] else "")
                    purchase_date = st.date_input("Purchase Date", value=edit_data['purchase_date'] if edit_data is not None and edit_data['purchase_date'] else None)
                    warranty_exp = st.date_input("Warranty Expiration", value=edit_data['warranty_expiration'] if edit_data is not None and edit_data['warranty_expiration'] else None)
                
                col1, col2 = st.columns(2)
                with col1:
                    mac_address = st.text_input("MAC Address", value=edit_data['mac_address'] if edit_data is not None and edit_data['mac_address'] else "")
                with col2:
                    ip_address = st.text_input("IP Address", value=edit_data['ip_address'] if edit_data is not None and edit_data['ip_address'] else "")
                
                notes = st.text_area("Notes", value=edit_data['notes'] if edit_data is not None and edit_data['notes'] else "", height=100)
                
                col1, col2, col3 = st.columns([1, 1, 4])
                with col1:
                    submit = st.form_submit_button("Save Asset")
                with col2:
                    cancel = st.form_submit_button("Cancel")
                
                if submit:
                    if asset_tag and asset_type and category and model and serial_number and status and location:
                        if edit_data is not None:
                            # Update existing asset
                            query = """
                                UPDATE dbo.Assets 
                                SET asset_tag=?, type=?, category=?, model=?, serial=?, 
                                    status=?, location=?, assigned_user=?, assigned_email=?, mac_address=?, 
                                    ip_address=?, purchase_date=?, warranty_expiration=?, notes=?, updated_at=GETDATE()
                                WHERE asset_id=?
                            """
                            params = (asset_tag, asset_type, category, model, serial_number, 
                                    status, location, assigned_user or None, assigned_email or None, 
                                    mac_address or None, ip_address or None, purchase_date, warranty_exp, 
                                    notes or None, st.session_state.edit_asset_id)
                        else:
                            # Insert new asset
                            query = """
                                INSERT INTO dbo.Assets 
                                (asset_tag, type, category, model, serial, status, location, 
                                assigned_user, assigned_email, mac_address, ip_address, purchase_date, 
                                warranty_expiration, notes, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                            """
                            params = (asset_tag, asset_type, category, model, serial_number, 
                                    status, location, assigned_user or None, assigned_email or None, 
                                    mac_address or None, ip_address or None, purchase_date, warranty_exp, notes or None)
                        
                        success, error = execute_non_query(query, params)
                        
                        if success:
                            st.success("✅ Asset saved successfully!")
                            st.session_state.show_add_asset_form = False
                            st.session_state.edit_asset_id = None
                            st.rerun()
                        else:
                            st.error(f"Error: {error}")
                    else:
                        st.error("Please fill in all required fields (*)")
                
                if cancel:
                    st.session_state.show_add_asset_form = False
                    st.session_state.edit_asset_id = None
                    st.rerun()
    
    st.markdown("---")
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Deployed", "In-Stock", "Surplus", "Repair", "Retired"])
    with col2:
        type_filter = st.selectbox("Type", ["All", "Laptop", "Desktop", "Monitor", "Printer", "Tablet", "Other"])
    with col3:
        location_filter = st.selectbox("Location", ["All", "Crater", "Dinwiddie County", "Greensville/Emporia", "Surry County", "Prince George", "Sussex County", "Hopewell", "Central IT"])
    with col4:
        search = st.text_input("🔍 Search", placeholder="Search assets...")
    
    # Build query
    query = "SELECT asset_id, asset_tag, type, model, serial, status, location, assigned_user, purchase_date, warranty_expiration FROM dbo.Assets WHERE 1=1"
    
    if status_filter != "All":
        query += f" AND status = '{status_filter}'"
    if type_filter != "All":
        query += f" AND type = '{type_filter}'"
    if location_filter != "All":
        query += f" AND location = '{location_filter}'"
    if search:
        query += f" AND (asset_tag LIKE '%{search}%' OR model LIKE '%{search}%' OR serial LIKE '%{search}%' OR assigned_user LIKE '%{search}%')"
    
    query += " ORDER BY created_at DESC"
    
    df, error = execute_query(query)
    
    if error:
        st.error(f"Error: {error}")
    else:
        st.write(f"**Total:** {len(df)} assets")
        
        # Display assets with edit buttons
        if len(df) > 0:
            for idx, row in df.iterrows():
                col1, col2 = st.columns([9, 1])
                with col1:
                    with st.container():
                        col_a, col_b, col_c, col_d, col_e = st.columns([2, 2, 2, 2, 2])
                        with col_a:
                            st.write(f"**{row['asset_tag']}**")
                        with col_b:
                            st.write(f"{row['type']} - {row['model']}")
                        with col_c:
                            st.write(f"Status: {row['status']}")
                        with col_d:
                            st.write(f"Location: {row['location']}")
                        with col_e:
                            st.write(f"User: {row['assigned_user'] if row['assigned_user'] else 'Unassigned'}")
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{row['asset_id']}"):
                        st.session_state.edit_asset_id = row['asset_id']
                        st.session_state.show_add_asset_form = False
                        st.rerun()
                
                st.markdown("---")

elif page == "👥 Users":
    st.header("👥 Users")
    
    query = """
        SELECT 
            id, username,
            CONCAT(first_name, ' ', last_name) as full_name,
            email, role,
            CASE WHEN is_active = 1 THEN 'Active' ELSE 'Inactive' END as status,
            last_login
        FROM dbo.users
        ORDER BY username
    """
    
    df, error = execute_query(query)
    if error:
        st.error(f"Error: {error}")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "🔍 Query Builder":
    st.header("🔍 Custom Query Builder")
    
    query = st.text_area("SQL Query", value="SELECT TOP 10 * FROM dbo.Tickets ORDER BY created_at DESC", height=150)
    
    if st.button("Execute Query"):
        df, error = execute_query(query)
        if error:
            st.error(f"Error: {error}")
        else:
            st.success(f"Returned {len(df)} rows")
            st.dataframe(df, use_container_width=True)

elif page == "🔌 Connection Test":
    st.header("🔌 Connection Test")
    
    if st.button("Test Connection"):
        with st.spinner("Testing..."):
            df, error = execute_query("SELECT @@VERSION as version, GETDATE() as current_time")
            if error:
                st.error(f"❌ Connection failed: {error}")
            else:
                st.success("✅ Connection successful!")
                st.dataframe(df)

# Footer
st.markdown("---")
st.markdown("*VDH Service Center - v5.0 | Virginia Department of Health © 2025*")
