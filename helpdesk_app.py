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

def execute_query(query):
    if not HAS_PYODBC:
        return None, "pyodbc not installed"
    
    server, database, username, password = get_connection_string()
    
    # Try ODBC Driver 17 (should be available in Azure App Service)
    try:
        conn_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;"
        conn = pyodbc.connect(conn_string, timeout=30)
        df = pd.read_sql(query, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric {
        background: white;
        padding: 15px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

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
                SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_tickets,
                SUM(CASE WHEN priority = 'urgent' THEN 1 ELSE 0 END) as urgent_tickets,
                SUM(CASE WHEN priority = 'high' THEN 1 ELSE 0 END) as high_tickets
            FROM dbo.Tickets
        """
        stats_df, error = execute_query(ticket_stats_query)
        
        if error:
            st.error(f"Error loading statistics: {error}")
        else:
            stats = stats_df.iloc[0]
            
            # Top metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="📋 Total Tickets", 
                    value=int(stats['total_tickets']),
                    delta=None
                )
            
            with col2:
                st.metric(
                    label="🟢 Open Tickets", 
                    value=int(stats['open_tickets']),
                    delta=None,
                    delta_color="inverse"
                )
            
            with col3:
                st.metric(
                    label="🔄 In Progress", 
                    value=int(stats['in_progress_tickets']),
                    delta=None
                )
            
            with col4:
                st.metric(
                    label="🚨 Urgent", 
                    value=int(stats['urgent_tickets']),
                    delta=None,
                    delta_color="inverse"
                )
            
            st.markdown("---")
            
            # Charts Row 1
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Tickets by Status")
                # Get status distribution
                status_query = """
                    SELECT status, COUNT(*) as count
                    FROM dbo.Tickets
                    GROUP BY status
                    ORDER BY count DESC
                """
                status_df, error = execute_query(status_query)
                
                if not error and status_df is not None and len(status_df) > 0:
                    fig = px.pie(
                        status_df, 
                        values='count', 
                        names='status',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig.update_layout(height=350)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No status data available")
            
            with col2:
                st.subheader("🎯 Tickets by Priority")
                # Get priority distribution
                priority_query = """
                    SELECT priority, COUNT(*) as count
                    FROM dbo.Tickets
                    GROUP BY priority
                    ORDER BY 
                        CASE priority
                            WHEN 'urgent' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            WHEN 'low' THEN 4
                        END
                """
                priority_df, error = execute_query(priority_query)
                
                if not error and priority_df is not None and len(priority_df) > 0:
                    colors = {
                        'urgent': '#dc3545',
                        'high': '#fd7e14', 
                        'medium': '#ffc107',
                        'low': '#28a745'
                    }
                    fig = px.bar(
                        priority_df, 
                        x='priority', 
                        y='count',
                        color='priority',
                        color_discrete_map=colors
                    )
                    fig.update_layout(
                        height=350,
                        showlegend=False,
                        xaxis_title="Priority",
                        yaxis_title="Count"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No priority data available")
            
            st.markdown("---")
            
            # Charts Row 2
            col1, col2 = st.columns(2)
            
            with col1:
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
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(
                        height=400,
                        showlegend=False,
                        xaxis_title="Number of Tickets",
                        yaxis_title="Location"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No location data available")
            
            with col2:
                st.subheader("📈 Ticket Trends (Last 30 Days)")
                trends_query = """
                    SELECT 
                        CAST(created_at AS DATE) as date,
                        COUNT(*) as count
                    FROM dbo.Tickets
                    WHERE created_at >= DATEADD(day, -30, GETDATE())
                    GROUP BY CAST(created_at AS DATE)
                    ORDER BY date
                """
                trends_df, error = execute_query(trends_query)
                
                if not error and trends_df is not None and len(trends_df) > 0:
                    fig = px.line(
                        trends_df, 
                        x='date', 
                        y='count',
                        markers=True
                    )
                    fig.update_layout(
                        height=400,
                        xaxis_title="Date",
                        yaxis_title="Tickets Created",
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No trend data available")
            
            st.markdown("---")
            
            # Performance Metrics
            st.subheader("⚡ Performance Metrics")
            
            perf_col1, perf_col2, perf_col3 = st.columns(3)
            
            # Average response time
            with perf_col1:
                response_query = """
                    SELECT 
                        AVG(DATEDIFF(hour, created_at, first_response_at)) as avg_response_hours
                    FROM dbo.Tickets
                    WHERE first_response_at IS NOT NULL
                """
                response_df, error = execute_query(response_query)
                
                if not error and response_df is not None:
                    avg_hours = response_df.iloc[0]['avg_response_hours']
                    if avg_hours is not None:
                        st.metric(
                            label="⏱️ Avg Response Time",
                            value=f"{avg_hours:.1f} hours"
                        )
                    else:
                        st.metric(label="⏱️ Avg Response Time", value="N/A")
                else:
                    st.metric(label="⏱️ Avg Response Time", value="N/A")
            
            # Average resolution time
            with perf_col2:
                resolution_query = """
                    SELECT 
                        AVG(DATEDIFF(hour, created_at, resolved_at)) as avg_resolution_hours
                    FROM dbo.Tickets
                    WHERE resolved_at IS NOT NULL
                """
                resolution_df, error = execute_query(resolution_query)
                
                if not error and resolution_df is not None:
                    avg_hours = resolution_df.iloc[0]['avg_resolution_hours']
                    if avg_hours is not None:
                        st.metric(
                            label="✅ Avg Resolution Time",
                            value=f"{avg_hours:.1f} hours"
                        )
                    else:
                        st.metric(label="✅ Avg Resolution Time", value="N/A")
                else:
                    st.metric(label="✅ Avg Resolution Time", value="N/A")
            
            # Resolution rate
            with perf_col3:
                if stats['total_tickets'] > 0:
                    resolution_rate = (stats['resolved_tickets'] / stats['total_tickets']) * 100
                    st.metric(
                        label="📊 Resolution Rate",
                        value=f"{resolution_rate:.1f}%"
                    )
                else:
                    st.metric(label="📊 Resolution Rate", value="0%")
            
            st.markdown("---")
            
            # Recent Tickets
            st.subheader("🕐 Recent Tickets")
            recent_query = """
                SELECT TOP 10
                    ticket_id,
                    short_description as subject,
                    name as customer,
                    status,
                    priority,
                    created_at
                FROM dbo.Tickets
                ORDER BY created_at DESC
            """
            recent_df, error = execute_query(recent_query)
            
            if not error and recent_df is not None:
                st.dataframe(
                    recent_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.error(f"Error loading recent tickets: {error}")

elif page == "🎫 Tickets":
    st.header("🎫 All Tickets")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "open", "in_progress", "resolved", "closed"])
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "low", "medium", "high", "urgent"])
    with col3:
        search = st.text_input("🔍 Search", placeholder="Search tickets...")
    
    # Build query
    query = "SELECT ticket_id, short_description, name, email, status, priority, location, created_at FROM dbo.Tickets WHERE 1=1"
    
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
        st.dataframe(df, use_container_width=True, hide_index=True)

elif page == "👥 Users":
    st.header("👥 Users")
    
    query = """
        SELECT 
            id,
            username,
            CONCAT(first_name, ' ', last_name) as full_name,
            email,
            role,
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
    
    st.markdown("""
    Write custom SQL queries to analyze the help desk data.
    
    **Available Tables:**
    - `dbo.users`
    - `dbo.Tickets`
    """)
    
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
st.markdown("*VDH IT Help Desk System - Enhanced Dashboard v1.0*")
