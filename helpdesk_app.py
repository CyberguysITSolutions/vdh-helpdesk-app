import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(page_title="VDH IT Help Desk", page_icon="🎫", layout="wide")

# Try to import pyodbc
try:
    import pyodbc
    HAS_PYODBC = True
except:
    HAS_PYODBC = False

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

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
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
        border-left: 4px solid #007bff;
        margin-bottom: 10px;
    }
    .note-card {
        background: #f8f9fa;
        padding: 10px;
        border-radius: 6px;
        margin: 10px 0;
        border-left: 3px solid #6c757d;
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

# Header
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🎫 VDH IT Help Desk System")
with col2:
    st.markdown("### Welcome, Admin")

st.markdown("---")

# Sidebar navigation
page = st.sidebar.selectbox("Navigate", [
    "📊 Dashboard", 
    "🎫 Tickets",
    "💻 Assets",
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
        
        # Charts Row 1
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Tickets by Status")
            status_query = "SELECT status, COUNT(*) as count FROM dbo.Tickets GROUP BY status"
            status_df, error = execute_query(status_query)
            
            if not error and status_df is not None and len(status_df) > 0:
                fig = px.pie(status_df, values='count', names='status',
                           color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("💻 Assets by Status")
            asset_status_query = "SELECT status, COUNT(*) as count FROM dbo.Assets GROUP BY status"
            asset_status_df, error = execute_query(asset_status_query)
            
            if not error and asset_status_df is not None and len(asset_status_df) > 0:
                fig = px.pie(asset_status_df, values='count', names='status',
                           color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
        
        # Charts Row 2
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
                colors = {'urgent': '#dc3545', 'high': '#fd7e14', 'medium': '#ffc107', 'low': '#28a745'}
                fig = px.bar(priority_df, x='priority', y='count', color='priority',
                           color_discrete_map=colors)
                fig.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📦 Assets by Type")
            asset_type_query = "SELECT type, COUNT(*) as count FROM dbo.Assets GROUP BY type ORDER BY count DESC"
            asset_type_df, error = execute_query(asset_type_query)
            
            if not error and asset_type_df is not None and len(asset_type_df) > 0:
                fig = px.bar(asset_type_df, x='type', y='count', color='count',
                           color_continuous_scale='Viridis')
                fig.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

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
                                ["open", "in_progress", "resolved", "closed"],
                                index=["open", "in_progress", "resolved", "closed"].index(ticket['status'])
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
            
            # Check if ticket_notes table exists, if not show message
            notes_query = """
                IF EXISTS (SELECT * FROM sys.tables WHERE name = 'ticket_notes')
                    SELECT note_id, note_text, created_by, created_at 
                    FROM dbo.ticket_notes 
                    WHERE ticket_id = ?
                    ORDER BY created_at DESC
            """
            
            # For now, show add note form
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
                        status = st.selectbox("Status*", ["open", "in_progress", "resolved", "closed"])
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
            status_filter = st.selectbox("Status", ["All", "open", "in_progress", "resolved", "closed"])
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
st.markdown("*VDH IT Help Desk System - v3.0 with Advanced Ticket Management*")
