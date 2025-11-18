import streamlit as st
import pyodbc
import os
from datetime import datetime, date, time, timedelta

# Page configuration
st.set_page_config(page_title="VDH Vehicle Request", page_icon="🚗", layout="centered")

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
st.title("🚗 Request a VDH Vehicle")
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

def get_available_vehicles():
    """Get list of available vehicles"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, make_model, license_plate 
                FROM dbo.vehicles 
                WHERE status = 'Available' OR Status = 'Available'
                ORDER BY make_model
            """)
            vehicles = cursor.fetchall()
            cursor.close()
            conn.close()
            return vehicles
        except:
            return []
    return []

# Get available vehicles
available_vehicles = get_available_vehicles()

if not available_vehicles:
    st.warning("⚠️ No vehicles currently available. Please check back later or contact fleet management.")
    st.info("📞 Fleet Management: (804) 555-FLEET | 📧 fleet@vdh.virginia.gov")
else:
    st.success(f"✅ {len(available_vehicles)} vehicle(s) available for request")
    
    # Form
    with st.form("vehicle_request_form"):
        st.subheader("Your Information")
        
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name *", placeholder="John")
            last_name = st.text_input("Last Name *", placeholder="Doe")
            email = st.text_input("Email Address *", placeholder="john.doe@vdh.virginia.gov")
        
        with col2:
            phone = st.text_input("Phone Number *", placeholder="(804) 555-1234")
            department = st.text_input("Department", placeholder="IT Services")
            employee_id = st.text_input("Employee ID", placeholder="VDH12345")
        
        st.markdown("---")
        st.subheader("Trip Details")
        
        # Vehicle selection
        vehicle_options = {f"{v[1]} - {v[2]}": v[0] for v in available_vehicles}
        selected_vehicle = st.selectbox(
            "Select Vehicle *",
            options=list(vehicle_options.keys()),
            help="Only available vehicles are shown"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            departure_date = st.date_input(
                "Departure Date *",
                min_value=date.today(),
                value=date.today()
            )
            departure_time = st.time_input("Departure Time *", value=time(8, 0))
        
        with col2:
            return_date = st.date_input(
                "Return Date *",
                min_value=date.today(),
                value=date.today()
            )
            return_time = st.time_input("Return Time *", value=time(17, 0))
        
        # Trip details
        destination = st.text_input(
            "Destination *",
            placeholder="123 Main St, Richmond, VA 23219"
        )
        
        purpose = st.text_area(
            "Purpose of Trip *",
            placeholder="Describe the purpose of your trip (e.g., attending training, site visit, etc.)",
            height=100
        )
        
        passengers = st.number_input(
            "Number of Passengers",
            min_value=1,
            max_value=15,
            value=1,
            help="Including yourself"
        )
        
        estimated_miles = st.number_input(
            "Estimated Round-Trip Miles",
            min_value=1,
            value=50,
            step=10
        )
        
        # Additional details
        st.markdown("### Additional Information (Optional)")
        special_equipment = st.text_area(
            "Special Equipment Needed",
            placeholder="GPS, wheelchair lift, cargo space, etc.",
            height=60
        )
        
        additional_notes = st.text_area(
            "Additional Notes",
            placeholder="Any other information we should know",
            height=60
        )
        
        st.markdown("---")
        
        # Agreement
        st.markdown("""
        **By submitting this request, I agree to:**
        - Return the vehicle in the same condition as received
        - Follow all VDH vehicle use policies
        - Report any accidents or incidents immediately
        - Refuel the vehicle before returning (if necessary)
        - Complete the trip log accurately
        """)
        
        acknowledge = st.checkbox("I acknowledge and agree to the terms above *")
        
        st.markdown("---")
        
        # Submit button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submitted = st.form_submit_button("🚀 Submit Request", width="stretch")
        
        if submitted:
            # Validate
            if not all([first_name, last_name, email, phone, selected_vehicle, 
                       departure_date, departure_time, return_date, return_time, 
                       destination, purpose]):
                st.error("⚠️ Please fill in all required fields (*)")
            elif not acknowledge:
                st.error("⚠️ You must acknowledge the terms to submit your request")
            elif "@" not in email:
                st.error("⚠️ Please enter a valid email address")
            elif return_date < departure_date:
                st.error("⚠️ Return date cannot be before departure date")
            elif return_date == departure_date and return_time <= departure_time:
                st.error("⚠️ Return time must be after departure time")
            else:
                # Get vehicle ID
                vehicle_id = vehicle_options[selected_vehicle]
                
                # Combine date and time
                departure_datetime = datetime.combine(departure_date, departure_time)
                return_datetime = datetime.combine(return_date, return_time)
                
                # Insert request
                conn = get_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        
                        insert_query = """
                            INSERT INTO dbo.Vehicle_Trips (
                                vehicle_id, requester_first, requester_last, requester_email,
                                requester_phone, destination, purpose, departure_time, return_time,
                                starting_mileage, status, created_at, notes
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'Requested', GETDATE(), ?)
                        """
                        
                        notes_combined = f"Passengers: {passengers} | Est. Miles: {estimated_miles}"
                        if special_equipment:
                            notes_combined += f" | Equipment: {special_equipment}"
                        if additional_notes:
                            notes_combined += f" | Notes: {additional_notes}"
                        if department:
                            notes_combined += f" | Dept: {department}"
                        if employee_id:
                            notes_combined += f" | Emp ID: {employee_id}"
                        
                        cursor.execute(insert_query, (
                            vehicle_id, first_name, last_name, email,
                            phone, destination, purpose,
                            departure_datetime, return_datetime,
                            notes_combined
                        ))
                        
                        conn.commit()
                        cursor.close()
                        conn.close()
                        
                        st.success(f"""
                        ✅ **Vehicle Request Submitted Successfully!**
                        
                        **Vehicle:** {selected_vehicle}
                        
                        **Departure:** {departure_date} at {departure_time}
                        
                        **Return:** {return_date} at {return_time}
                        
                        You will receive a confirmation email at: **{email}**
                        
                        Fleet management will review your request and respond within 24 hours.
                        
                        **Important:** Please check your email for approval status before your trip date.
                        """)
                        
                        st.balloons()
                        
                    except Exception as e:
                        st.error(f"❌ Error submitting request: {str(e)}")
                        st.info("💡 Please contact fleet management directly at fleet@vdh.virginia.gov")
                else:
                    st.error("❌ Could not connect to database. Please try again later.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>Need Help?</strong></p>
    <p>📞 Fleet Management: (804) 555-FLEET (35338)</p>
    <p>📧 Email: fleet@vdh.virginia.gov</p>
    <p>🕒 Office Hours: Monday-Friday, 8:00 AM - 5:00 PM</p>
    <p style='margin-top: 20px; font-size: 0.9em;'>
        Virginia Department of Health © 2025 | Fleet Services
    </p>
</div>
""", unsafe_allow_html=True)
