import streamlit as st
import pyodbc
import os
from datetime import datetime

# Page configuration
st.set_page_config(page_title="VDH Ticket Submission", page_icon="🎫", layout="centered")

# VDH Branding
VDH_NAVY = "#002855"
VDH_ORANGE = "#FF6B35"

st.markdown(f"""
<style>
    .main {{
        background-color: #f5f5f5;
    }}
    .stButton>button {{
        background-color: {VDH_NAVY};
        color: white;
        border-radius: 5px;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
    }}
    .stButton>button:hover {{
        background-color: {VDH_ORANGE};
    }}
    h1, h2 {{
        color: {VDH_NAVY};
    }}
</style>
""", unsafe_allow_html=True)

# Header
st.image("https://via.placeholder.com/600x100/002855/FFFFFF?text=Virginia+Department+of+Health", width=600)
st.title("🎫 Submit a Help Desk Ticket")
st.markdown("---")

# Database connection
def get_connection():
    try:
        server = os.getenv("DB_SERVER", "sql-helpdesk-server-1758757113.database.windows.net")
        database = os.getenv("DB_DATABASE", "helpdesk-db")
        username = os.getenv("DB_USERNAME", "helpdeskadmin")
        password = os.getenv("DB_PASSWORD", "")
        
        # Azure SQL format
        if "@" not in username:
            username = f"{username}@{server.split('.')[0]}"
        
        conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER=tcp:{server},1433;DATABASE={database};UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60;"
        return pyodbc.connect(conn_str, autocommit=False)
    except Exception as e:
        st.error(f"Database connection error: {str(e)}")
        return None

# Form
with st.form("ticket_submission_form"):
    st.subheader("Your Information")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name *", placeholder="John Doe")
        email = st.text_input("Email Address *", placeholder="john.doe@vdh.virginia.gov")
    
    with col2:
        phone = st.text_input("Phone Number", placeholder="(804) 555-1234")
        location = st.selectbox("VDH Location *", [
            "Petersburg", "Hopewell", "Dinwiddie", "Surry",
            "Greensville/Emporia", "Prince George", "Sussex"
        ])
    
    st.markdown("---")
    st.subheader("Issue Details")
    
    col1, col2 = st.columns(2)
    with col1:
        ticket_type = st.selectbox("Issue Type *", [
            "Technical issue",
            "Hardware issue",
            "Software issue",
            "Network issue",
            "Access request",
            "Training request",
            "Other"
        ])
    
    with col2:
        priority = st.selectbox("Priority *", [
            "Low - Can wait",
            "Medium - Normal priority",
            "High - Needs attention soon",
            "Critical - Urgent"
        ])
    
    subject = st.text_input("Subject *", placeholder="Brief description of the issue")
    description = st.text_area(
        "Detailed Description *",
        placeholder="Please provide as much detail as possible about your issue...",
        height=200
    )
    
    st.markdown("---")
    
    # Submit button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        submitted = st.form_submit_button("🚀 Submit Ticket", width="stretch")
    
    if submitted:
        # Validate
        if not all([name, email, location, ticket_type, priority, subject, description]):
            st.error("⚠️ Please fill in all required fields (*)")
        elif "@" not in email:
            st.error("⚠️ Please enter a valid email address")
        else:
            # Generate ticket number
            ticket_number = f"TKT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Clean priority
            priority_clean = priority.split(" - ")[0]
            
            # Insert ticket
            conn = get_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    
                    # Try to discover column names first
                    cursor.execute("""
                        SELECT TOP 1 COLUMN_NAME 
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_NAME = 'Tickets' 
                        ORDER BY ORDINAL_POSITION
                    """)
                    
                    # Insert with flexible column names (try common patterns)
                    insert_query = """
                        INSERT INTO dbo.Tickets (
                            TicketNumber, CustomerName, CustomerEmail, CustomerPhone,
                            Location, [Type], Subject, Description,
                            Status, Priority, CreatedDate, UpdatedDate
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?, GETDATE(), GETDATE())
                    """
                    
                    cursor.execute(insert_query, (
                        ticket_number, name, email, phone or None,
                        location, ticket_type, subject, description,
                        priority_clean
                    ))
                    
                    conn.commit()
                    cursor.close()
                    conn.close()
                    
                    st.success(f"""
                    ✅ **Ticket Submitted Successfully!**
                    
                    Your ticket number is: **{ticket_number}**
                    
                    You will receive a confirmation email at: **{email}**
                    
                    Our team will review your request and respond within 24-48 hours.
                    """)
                    
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Error submitting ticket: {str(e)}")
                    st.info("💡 Please contact IT support directly at helpdesk@vdh.virginia.gov")
            else:
                st.error("❌ Could not connect to database. Please try again later.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>Need Immediate Assistance?</strong></p>
    <p>📞 Call: (804) 555-HELP (4357)</p>
    <p>📧 Email: helpdesk@vdh.virginia.gov</p>
    <p style='margin-top: 20px; font-size: 0.9em;'>
        Virginia Department of Health © 2025 | Help Desk Services
    </p>
</div>
""", unsafe_allow_html=True)
