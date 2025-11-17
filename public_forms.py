"""
public_forms.py
Public-facing forms module that provides render functions for ticket, vehicle, and procurement submissions.
Each function renders a form, validates inputs, inserts into DB, and shows confirmation.
"""
import streamlit as st
import uuid
from datetime import date, datetime
from typing import Optional, Tuple, Callable
import os


def get_mock_data_mode() -> bool:
    """Check if we're running in MOCK_DATA mode."""
    return os.getenv("MOCK_DATA", "0") == "1"


def insert_and_get_id(query: str, params: Optional[tuple] = None) -> Tuple[Optional[int], Optional[str]]:
    """
    Execute an INSERT query and return the newly inserted ID.
    Returns (new_id, None) on success, or (None, error_message) on failure.
    Supports MOCK_DATA mode for testing without a DB.
    """
    if get_mock_data_mode():
        # Mock mode: return a fake ID
        mock_id = 1000 + hash(str(params)) % 9000
        return mock_id, None
    
    try:
        from fleet import fleet_db
    except Exception as e:
        return None, f"fleet_db import error: {e}"
    
    try:
        conn = fleet_db.get_conn()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get the last inserted ID
            cursor.execute("SELECT @@IDENTITY AS id")
            row = cursor.fetchone()
            new_id = int(row[0]) if row and row[0] else None
            
            conn.commit()
            cursor.close()
            conn.close()
            return new_id, None
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
            import traceback
            return None, f"execution error: {e}\n{traceback.format_exc()}"
    except Exception as e:
        import traceback
        return None, f"connection error: {e}\n{traceback.format_exc()}"


def execute_non_query(query: str, params: Optional[tuple] = None) -> Tuple[bool, Optional[str]]:
    """
    Execute INSERT/UPDATE/DELETE using fleet.fleet_db.get_conn().
    Returns (True, None) on success, or (False, error_message) on failure.
    Supports MOCK_DATA mode for testing without a DB.
    """
    if get_mock_data_mode():
        # Mock mode: just return success
        return True, None
    
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
            import traceback
            return False, f"execution error: {e}\n{traceback.format_exc()}"
    except Exception as e:
        import traceback
        return False, f"connection error: {e}\n{traceback.format_exc()}"


def render_public_ticket_form(insert_callback: Optional[Callable] = None):
    """
    Render the public ticket submission form.
    Validates required fields, inserts into dbo.Tickets with status='New', and shows confirmation.
    
    Args:
        insert_callback: Optional custom insert function. If None, uses insert_and_get_id.
    """
    st.header("🎫 Submit a Support Ticket")
    st.markdown("Use this form to request IT help. Your submission will be reviewed by our support team.")
    
    with st.form("public_ticket_form", clear_on_submit=True):
        name = st.text_input("Your Name *", help="First and last name")
        email = st.text_input("Your Email *", help="We will use this to send updates")
        phone = st.text_input("Phone Number (optional)")
        location = st.text_input("Location (optional)", help="Building/room number")
        priority = st.selectbox("Priority *", ["low", "medium", "high", "urgent"])
        short_desc = st.text_input("Short Description *", help="Brief summary of the issue")
        description = st.text_area("Full Description", help="Provide details about your request")
        submit = st.form_submit_button("Submit Ticket")
    
    if submit:
        # Validate required fields
        if not name or not email or not short_desc:
            st.error("❌ Please fill in all required fields (marked with *).")
            return
        
        # Use custom callback if provided, otherwise use default insert
        if insert_callback:
            ticket_id, err = insert_callback(
                name=name,
                email=email,
                phone=phone,
                location=location,
                priority=priority,
                short_desc=short_desc,
                description=description
            )
        else:
            # Default: insert into dbo.Tickets with status='New'
            insert_query = """
                INSERT INTO dbo.Tickets
                (status, priority, name, email, location, phone_number, short_description, description, created_at)
                VALUES ('New', ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """
            params = (priority, name, email, location or None, phone or None, short_desc, description or None)
            ticket_id, err = insert_and_get_id(insert_query, params)
        
        if err:
            st.error(f"❌ Submission failed: {err}")
        else:
            st.success(f"✅ Ticket submitted successfully! Reference ID: #{ticket_id}")
            st.info("📧 Our support team will review your request and respond via email.")


def render_public_vehicle_request_form(insert_callback: Optional[Callable] = None):
    """
    Render the public vehicle request form.
    Validates required fields, inserts into dbo.Vehicle_Trips with status='Requested', and shows confirmation.
    
    Args:
        insert_callback: Optional custom insert function. If None, uses insert_and_get_id.
    """
    st.header("🚗 Request a Vehicle")
    st.markdown("Submit a vehicle request for your upcoming trip. The Fleet team will review and approve.")
    
    with st.form("public_vehicle_request", clear_on_submit=True):
        requester_first = st.text_input("First Name *")
        requester_last = st.text_input("Last Name *")
        requester_email = st.text_input("Email *")
        requester_phone = st.text_input("Phone Number (optional)")
        destination = st.text_input("Destination / Purpose *")
        departure_date = st.date_input("Departure Date *", value=date.today())
        return_date = st.date_input("Return Date *", value=date.today())
        starting_mileage = st.number_input("Starting Mileage (if known)", min_value=0, value=0)
        notes = st.text_area("Additional Notes (optional)")
        submit = st.form_submit_button("Submit Request")
    
    if submit:
        # Validate required fields
        if not requester_first or not requester_last or not requester_email or not destination:
            st.error("❌ Please fill in all required fields (marked with *).")
            return
        
        # Use custom callback if provided, otherwise use default insert
        if insert_callback:
            request_id, err = insert_callback(
                requester_first=requester_first,
                requester_last=requester_last,
                requester_email=requester_email,
                requester_phone=requester_phone,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                starting_mileage=starting_mileage,
                notes=notes
            )
        else:
            # Default: insert into dbo.Vehicle_Trips with status='Requested'
            insert_query = """
                INSERT INTO dbo.Vehicle_Trips
                (vehicle_id, requester_first, requester_last, requester_email, requester_phone, destination, departure_time, return_time, status, starting_mileage, notes, created_at)
                VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, 'Requested', ?, ?, GETDATE())
            """
            dep_ts = departure_date.isoformat()
            ret_ts = return_date.isoformat()
            params = (
                requester_first, requester_last, requester_email, 
                requester_phone or None, destination, dep_ts, ret_ts, 
                int(starting_mileage), notes or None
            )
            request_id, err = insert_and_get_id(insert_query, params)
        
        if err:
            st.error(f"❌ Submission failed: {err}")
        else:
            st.success(f"✅ Vehicle request submitted successfully! Request ID: #{request_id}")
            st.info("🚙 The Fleet team will review your request and contact you with approval details.")


def render_public_procurement_form(insert_callback: Optional[Callable] = None):
    """
    Render the public procurement request form.
    Validates required fields, inserts into dbo.Procurement_Requests with status='Requested', and shows confirmation.
    
    Args:
        insert_callback: Optional custom insert function. If None, uses insert_and_get_id.
    """
    st.header("🛒 Submit a Procurement Request")
    st.markdown("Request items or services. The Procurement team will review and process your request.")
    
    with st.form("public_procurement_form", clear_on_submit=True):
        requester_name = st.text_input("Your Name *", help="Requester's full name")
        requester_email = st.text_input("Your Email *")
        location = st.text_input("Location *", help="Delivery location")
        department = st.text_input("Department *")
        justification = st.text_area("Justification *", help="Why you need this item/service")
        
        st.markdown("### Item Details")
        item_description = st.text_input("Item Description *")
        quantity = st.number_input("Quantity *", min_value=1, value=1)
        unit_price = st.number_input("Estimated Unit Price *", min_value=0.0, value=0.0, format="%.2f")
        
        submit = st.form_submit_button("Submit Request")
    
    if submit:
        # Validate required fields
        if not requester_name or not requester_email or not justification or not item_description or not location or not department:
            st.error("❌ Please fill in all required fields (marked with *).")
            return
        
        total = float(unit_price) * int(quantity)
        
        # Use custom callback if provided, otherwise use default insert
        if insert_callback:
            request_id, err = insert_callback(
                requester_name=requester_name,
                requester_email=requester_email,
                location=location,
                department=department,
                justification=justification,
                item_description=item_description,
                quantity=quantity,
                unit_price=unit_price,
                total=total
            )
        else:
            # Default: insert into dbo.Procurement_Requests with status='Requested'
            import json
            request_number = f"PR-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
            items_payload = [{
                "line_number": 1,
                "item_description": item_description,
                "quantity": int(quantity),
                "unit_price": float(unit_price),
                "total_price": total
            }]
            attachments_json = json.dumps(items_payload)
            
            insert_query = """
                INSERT INTO dbo.Procurement_Requests
                (request_number, requester_name, requester_email, location, department, justification, total_amount, status, priority, created_at, attachments)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Requested', 'normal', GETDATE(), ?)
            """
            params = (request_number, requester_name, requester_email, location, department, justification, total, attachments_json)
            request_id, err = insert_and_get_id(insert_query, params)
        
        if err:
            st.error(f"❌ Submission failed: {err}")
        else:
            st.success(f"✅ Procurement request submitted successfully! Request ID: #{request_id}")
            st.info("📦 The Procurement team will review your request and contact you with next steps.")
