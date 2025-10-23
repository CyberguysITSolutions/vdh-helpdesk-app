import streamlit as st
import pandas as pd
from datetime import datetime
import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Page configuration
st.set_page_config(page_title="IT Help Desk", page_icon="🎫", layout="wide")

# Database connection using SQLAlchemy
def get_db_connection():
    # Try to get credentials from Streamlit secrets first, then environment variables
    try:
        server = st.secrets["database"]["server"]
        database = st.secrets["database"]["database"]
        username = st.secrets["database"]["username"]
        password = st.secrets["database"]["password"]
    except:
        # Fallback to environment variables
        server = os.getenv("DB_SERVER", "sql-helpdesk-server-1758757113.database.windows.net")
        database = os.getenv("DB_DATABASE", "helpdesk-db")
        username = os.getenv("DB_USERNAME")
        password = os.getenv("DB_PASSWORD")
    
    # URL encode the password to handle special characters
    password_encoded = quote_plus(password)
    
    # Create connection string for Azure SQL using pymssql driver
    connection_string = f"mssql+pymssql://{username}:{password_encoded}@{server}:1433/{database}?charset=utf8"
    
    try:
        # Create engine
        engine = create_engine(
            connection_string,
            connect_args={
                "timeout": 30,
                "login_timeout": 30
            }
        )
        return engine
    except Exception as e:
        raise Exception(f"Database connection failed: {str(e)}")

# Execute query function
def execute_query(query):
    try:
        engine = get_db_connection()
        df = pd.read_sql_query(query, engine)
        return df, None
    except Exception as e:
        return None, str(e)

# Main app
st.title("🎫 IT Help Desk System")
st.markdown("---")

# Sidebar for navigation
page = st.sidebar.selectbox("Navigate", ["Dashboard", "Tickets", "Users", "Query Builder", "Connection Test"])

if page == "Dashboard":
    st.header("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get statistics
    engine = get_db_connection()
    
    with col1:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dbo.Tickets WHERE status = 'open'"))
            open_tickets = result.scalar()
        st.metric("Open Tickets", open_tickets)
    
    with col2:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dbo.Tickets WHERE status = 'in_progress'"))
            in_progress = result.scalar()
        st.metric("In Progress", in_progress)
    
    with col3:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dbo.Tickets WHERE priority = 'urgent'"))
            urgent = result.scalar()
        st.metric("Urgent", urgent, delta_color="inverse")
    
    with col4:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM dbo.Tickets"))
            total = result.scalar()
        st.metric("Total Tickets", total)
    
    st.markdown("### Recent Tickets")
    query = """
        SELECT 
            t.ticket_id,
            t.short_description as subject,
            t.name as customer,
            t.status,
            t.priority,
            t.created_at
        FROM dbo.Tickets t
        ORDER BY t.created_at DESC
        OFFSET 0 ROWS FETCH NEXT 10 ROWS ONLY
    """
    df, error = execute_query(query)
    if error:
        st.error(f"Error: {error}")
    else:
        st.dataframe(df, use_container_width=True)

elif page == "Tickets":
    st.header("🎫 All Tickets")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Status", ["All", "open", "in_progress", "resolved", "closed"])
    
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "low", "medium", "high", "urgent"])
    
    with col3:
        st.write("")  # Spacer
    
    # Build query based on filters - Note: Tickets table already has name and email columns
    query = """
        SELECT 
            t.ticket_id as "Ticket ID",
            t.short_description as "Subject",
            t.name as "Customer",
            t.email as "Email",
            t.assigned_to as "Assigned To",
            t.status as "Status",
            t.priority as "Priority",
            t.created_at as "Created"
        FROM dbo.Tickets t
        WHERE 1=1
    """
    
    if status_filter != "All":
        query += f" AND t.status = '{status_filter}'"
    
    if priority_filter != "All":
        query += f" AND t.priority = '{priority_filter}'"
    
    query += " ORDER BY t.created_at DESC"
    
    df, error = execute_query(query)
    
    if error:
        st.error(f"Error loading tickets: {error}")
    else:
        st.dataframe(df, use_container_width=True)
        
        # Ticket details
        if not df.empty:
            st.markdown("### Ticket Details")
            ticket_id = st.selectbox("Select Ticket", df["Ticket ID"].tolist())
            
            if st.button("Load Details"):
                query = f"""
                    SELECT 
                        t.*
                    FROM dbo.Tickets t
                    WHERE t.ticket_id = {ticket_id}
                """
                ticket_df, error = execute_query(query)
                
                if error:
                    st.error(f"Error: {error}")
                else:
                    ticket = ticket_df.iloc[0]
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Subject:** {ticket['short_description']}")
                        st.write(f"**Customer:** {ticket['name']}")
                        st.write(f"**Email:** {ticket['email']}")
                        st.write(f"**Phone:** {ticket['phone_number'] if pd.notna(ticket['phone_number']) else 'N/A'}")
                        st.write(f"**Location:** {ticket['location'] if pd.notna(ticket['location']) else 'N/A'}")
                    
                    with col2:
                        st.write(f"**Status:** {ticket['status']}")
                        st.write(f"**Priority:** {ticket['priority']}")
                        st.write(f"**Assigned To:** {ticket['assigned_to'] if pd.notna(ticket['assigned_to']) else 'Unassigned'}")
                        st.write(f"**Created:** {ticket['created_at']}")
                        if pd.notna(ticket['first_response_at']):
                            st.write(f"**First Response:** {ticket['first_response_at']}")
                        if pd.notna(ticket['resolved_at']):
                            st.write(f"**Resolved:** {ticket['resolved_at']}")
                    
                    st.markdown("**Description:**")
                    st.write(ticket['description'])
                    
                    # Note: We'd need to check if there's a responses/comments table
                    st.info("Response history requires a responses/comments table")

elif page == "Users":
    st.header("👥 Users")
    
    query = """
        SELECT 
            id as "User ID",
            username as "Username",
            CONCAT(first_name, ' ', last_name) as "Name",
            email as "Email",
            role as "Role",
            is_active as "Active",
            created_at as "Created",
            last_login as "Last Login"
        FROM dbo.users
        ORDER BY username
    """
    
    df, error = execute_query(query)
    
    if error:
        st.error(f"Error loading users: {error}")
    else:
        st.dataframe(df, use_container_width=True)

elif page == "Query Builder":
    st.header("🔍 Custom Query Builder")
    
    st.markdown("""
    Write custom SQL queries to analyze the help desk data.
    
    **Available Tables:**
    - `dbo.users` (id, username, email, password_hash, first_name, last_name, role, entra_id, created_at, is_active, last_login)
    - `dbo.Tickets` (ticket_id, status, priority, name, email, location, phone_number, short_description, description, created_at, first_response_at, resolved_at, assigned_to)
    - `dbo.customers` (check schema for details)
    - `dbo.customer_support_tickets` (check schema for details)
    - And more...
    """)
    
    # Sample queries
    sample_queries = {
        "Select a query...": "",
        "All open tickets": "SELECT * FROM dbo.Tickets WHERE status = 'open'",
        "Tickets by priority": "SELECT priority, COUNT(*) as count FROM dbo.Tickets GROUP BY priority",
        "Recent tickets": """SELECT TOP 20 
    ticket_id, 
    short_description, 
    name as customer,
    status, 
    priority,
    created_at 
FROM dbo.Tickets 
ORDER BY created_at DESC""",
        "Tickets by assigned user": """SELECT 
    assigned_to, 
    COUNT(*) as ticket_count,
    SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count
FROM dbo.Tickets 
WHERE assigned_to IS NOT NULL
GROUP BY assigned_to
ORDER BY ticket_count DESC""",
        "Active users": """SELECT 
    id,
    username,
    CONCAT(first_name, ' ', last_name) as full_name,
    email,
    role
FROM dbo.users
WHERE is_active = 1
ORDER BY username"""
    }
    
    selected_sample = st.selectbox("Sample Queries", list(sample_queries.keys()))
    
    query = st.text_area("SQL Query", value=sample_queries[selected_sample], height=150)
    
    if st.button("Execute Query"):
        if query.strip():
            df, error = execute_query(query)
            
            if error:
                st.error(f"Failed to execute query. Error: {error}")
            else:
                st.success(f"Query executed successfully! Returned {len(df)} rows.")
                st.dataframe(df, use_container_width=True)
                
                # Download option
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download as CSV",
                    data=csv,
                    file_name="query_results.csv",
                    mime="text/csv"
                )
        else:
            st.warning("Please enter a query")

elif page == "Connection Test":
    st.header("🔌 Database Connection Test")
    
    st.markdown("""
    This page helps diagnose connection issues with your Azure SQL Database.
    """)
    
    # Show connection info (without password)
    st.subheader("Configuration")
    try:
        server = st.secrets["database"]["server"]
        database = st.secrets["database"]["database"]
        username = st.secrets["database"]["username"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Server:** {server}")
            st.write(f"**Database:** {database}")
        with col2:
            st.write(f"**Username:** {username}")
            st.write(f"**Driver:** SQLAlchemy + pymssql")
    except Exception as e:
        st.error(f"Could not read secrets: {e}")
        st.info("Make sure you've configured secrets in Streamlit Cloud settings")
    
    st.markdown("---")
    
    # Test connection
    if st.button("Test Connection"):
        with st.spinner("Testing connection..."):
            try:
                engine = get_db_connection()
                st.success("✅ Connection successful!")
                
                # Try a simple query
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT @@VERSION"))
                    version = result.scalar()
                    st.info(f"Database version: {version[:100]}...")
                
                # Test table access
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM dbo.Tickets"))
                    count = result.scalar()
                    st.success(f"✅ Can access Tickets table: {count} tickets found")
                
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM dbo.users"))
                    count = result.scalar()
                    st.success(f"✅ Can access users table: {count} users found")
                
            except Exception as e:
                st.error(f"❌ Connection failed: {str(e)}")
                
                # Provide troubleshooting tips
                st.markdown("### 🔧 Troubleshooting Tips:")
                st.markdown("""
                1. **Check Azure SQL Firewall:**
                   - Go to Azure Portal → SQL Server → Networking
                   - Add firewall rule to allow Streamlit Cloud IPs
                   - Or temporarily allow all IPs (0.0.0.0 - 255.255.255.255)
                
                2. **Verify credentials:**
                   - Check Streamlit secrets are correct
                   - Username should NOT include @servername
                   - Password should be correct
                
                3. **Check server name:**
                   - Should be: `servername.database.windows.net`
                   - Should NOT include port or database name
                
                4. **Try SQL Authentication:**
                   - Make sure you're using SQL Authentication, not Azure AD
                """)
    
    # Show environment info
    st.markdown("---")
    st.subheader("Environment Info")
    
    import sys
    st.write(f"**Python version:** {sys.version}")
    st.write(f"**Streamlit version:** {st.__version__}")
    st.write(f"**Pandas version:** {pd.__version__}")
    
    try:
        import sqlalchemy
        st.write(f"**SQLAlchemy version:** {sqlalchemy.__version__}")
    except:
        st.write("**SQLAlchemy:** Not installed")
    
    try:
        import pymssql
        st.write(f"**pymssql version:** {pymssql.__version__}")
    except:
        st.write("**pymssql:** Not installed")

# Footer
st.markdown("---")
st.markdown("*IT Help Desk System v1.0*")
