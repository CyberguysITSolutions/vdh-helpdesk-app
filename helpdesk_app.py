import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Page configuration
st.set_page_config(page_title="IT Help Desk", page_icon="🎫", layout="wide")

# Try to import pyodbc
try:
    import pyodbc
    HAS_PYODBC = True
except:
    HAS_PYODBC = False
    st.error("pyodbc not available - cannot connect to database")

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
    
    # Try multiple driver configurations
    configs = [
        f"DRIVER={{FreeTDS}};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password};TDS_Version=8.0;Encrypt=yes;",
        f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;",
        f"Driver={{FreeTDS}};Server={server};Port=1433;Database={database};Uid={username};Pwd={password};TDS_Version=7.4;",
    ]
    
    last_error = None
    for conn_string in configs:
        try:
            conn = pyodbc.connect(conn_string, timeout=30)
            df = pd.read_sql(query, conn)
            conn.close()
            return df, None
        except Exception as e:
            last_error = str(e)
            continue
    
    return None, f"Connection failed: {last_error}"

# Main app
st.title("🎫 IT Help Desk System")
st.markdown("---")

# Sidebar for navigation
page = st.sidebar.selectbox("Navigate", ["Dashboard", "Tickets", "Users", "Query Builder", "Connection Test"])

if page == "Dashboard":
    st.header("📊 Dashboard")
    
    st.info("Attempting to connect to database...")
    
    # Try a simple query first
    test_df, error = execute_query("SELECT COUNT(*) as total FROM dbo.Tickets")
    
    if error:
        st.error(f"Cannot connect to database: {error}")
        st.markdown("""
        ### Troubleshooting:
        1. Check Azure SQL firewall allows Streamlit Cloud IPs
        2. Verify credentials in Streamlit secrets
        3. Ensure SQL Authentication is enabled
        """)
    else:
        st.success("✅ Connected to database!")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            df, _ = execute_query("SELECT COUNT(*) as count FROM dbo.Tickets WHERE status = 'open'")
            if df is not None:
                st.metric("Open Tickets", df['count'].iloc[0])
        
        with col2:
            df, _ = execute_query("SELECT COUNT(*) as count FROM dbo.Tickets WHERE status = 'in_progress'")
            if df is not None:
                st.metric("In Progress", df['count'].iloc[0])
        
        with col3:
            df, _ = execute_query("SELECT COUNT(*) as count FROM dbo.Tickets WHERE priority = 'urgent'")
            if df is not None:
                st.metric("Urgent", df['count'].iloc[0])
        
        with col4:
            df, _ = execute_query("SELECT COUNT(*) as count FROM dbo.Tickets")
            if df is not None:
                st.metric("Total Tickets", df['count'].iloc[0])
        
        st.markdown("### Recent Tickets")
        query = """
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
        df, error = execute_query(query)
        if error:
            st.error(f"Error: {error}")
        else:
            st.dataframe(df, use_container_width=True)

elif page == "Tickets":
    st.header("🎫 All Tickets")
    
    status_filter = st.selectbox("Status", ["All", "open", "in_progress", "resolved", "closed"])
    priority_filter = st.selectbox("Priority", ["All", "low", "medium", "high", "urgent"])
    
    query = "SELECT ticket_id, short_description, name, email, status, priority, created_at FROM dbo.Tickets WHERE 1=1"
    
    if status_filter != "All":
        query += f" AND status = '{status_filter}'"
    if priority_filter != "All":
        query += f" AND priority = '{priority_filter}'"
    
    query += " ORDER BY created_at DESC"
    
    df, error = execute_query(query)
    if error:
        st.error(f"Error: {error}")
    else:
        st.dataframe(df, use_container_width=True)

elif page == "Users":
    st.header("👥 Users")
    
    query = """
        SELECT 
            id,
            username,
            CONCAT(first_name, ' ', last_name) as full_name,
            email,
            role,
            is_active
        FROM dbo.users
        ORDER BY username
    """
    
    df, error = execute_query(query)
    if error:
        st.error(f"Error: {error}")
    else:
        st.dataframe(df, use_container_width=True)

elif page == "Query Builder":
    st.header("🔍 Custom Query Builder")
    
    query = st.text_area("SQL Query", value="SELECT TOP 10 * FROM dbo.Tickets", height=150)
    
    if st.button("Execute Query"):
        df, error = execute_query(query)
        if error:
            st.error(f"Error: {error}")
        else:
            st.success(f"Returned {len(df)} rows")
            st.dataframe(df, use_container_width=True)

elif page == "Connection Test":
    st.header("🔌 Connection Test")
    
    if HAS_PYODBC:
        st.write("**Available ODBC Drivers:**")
        try:
            drivers = pyodbc.drivers()
            for driver in drivers:
                st.write(f"- {driver}")
        except:
            st.write("Could not list drivers")
    
    st.markdown("---")
    
    if st.button("Test Connection"):
        server, database, username, password = get_connection_string()
        st.write(f"Server: {server}")
        st.write(f"Database: {database}")
        st.write(f"Username: {username}")
        
        df, error = execute_query("SELECT @@VERSION as version")
        if error:
            st.error(f"❌ Connection failed: {error}")
        else:
            st.success("✅ Connection successful!")
            st.write(df['version'].iloc[0][:100])

# Footer
st.markdown("---")
st.markdown("*IT Help Desk System v1.0*")


