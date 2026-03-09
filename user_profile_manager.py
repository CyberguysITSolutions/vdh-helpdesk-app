"""
VDH Crater Service Center - User Profile Management
===================================================

This module provides user profile management and autofill functionality
for all forms across the helpdesk application.

Features:
- Automatic profile creation from form submissions
- Profile lookup and autofill
- Usage tracking
- Profile management interface

Author: Cyber Guys DMV
Date: March 2026
"""

import pandas as pd
import streamlit as st
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# ==============================================================================
# USER PROFILE FUNCTIONS
# ==============================================================================

def get_user_profile_by_email(email: str, execute_query_func) -> Optional[Dict[str, Any]]:
    """
    Retrieve user profile by email address
    
    Args:
        email: User's email address
        execute_query_func: Function to execute database queries
        
    Returns:
        Dictionary containing user profile data or None if not found
    """
    try:
        query = "SELECT * FROM dbo.user_profiles WHERE email = ? AND is_active = 1"
        result_df, error = execute_query_func(query, (email,))
        
        if error or result_df is None or result_df.empty:
            return None
            
        # Convert to dictionary
        profile = result_df.iloc[0].to_dict()
        return profile
    
    except Exception as e:
        logger.error(f"Error retrieving user profile for {email}: {e}")
        return None


def create_or_update_user_profile(
    email: str,
    full_name: str,
    phone: str = None,
    department: str = None,
    location: str = None,
    form_source: str = None,
    execute_non_query_func = None
) -> bool:
    """
    Create or update user profile
    
    Args:
        email: User's email address
        full_name: User's full name
        phone: Phone number (optional)
        department: Department name (optional)
        location: Office location (optional)
        form_source: Name of form that created the profile (optional)
        execute_non_query_func: Function to execute database commands
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Use stored procedure for get_or_create logic
        query = """
            EXEC dbo.sp_get_or_create_user_profile 
                @email = ?,
                @full_name = ?,
                @phone = ?,
                @department = ?,
                @location = ?,
                @form_source = ?
        """
        
        success, error = execute_non_query_func(
            query,
            (email, full_name, phone, department, location, form_source)
        )
        
        if error:
            logger.error(f"Error creating/updating profile for {email}: {error}")
            return False
            
        logger.info(f"Profile created/updated for {email} from {form_source}")
        return True
        
    except Exception as e:
        logger.error(f"Exception creating/updating profile: {e}")
        return False


def increment_usage_counter(email: str, counter_type: str, execute_non_query_func) -> bool:
    """
    Increment usage counter for a user profile
    
    Args:
        email: User's email address
        counter_type: Type of counter ('ticket', 'vehicle_request', 'procurement')
        execute_non_query_func: Function to execute database commands
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if counter_type == 'ticket':
            query = "EXEC dbo.sp_increment_ticket_count @email = ?"
        elif counter_type == 'vehicle_request':
            query = "EXEC dbo.sp_increment_vehicle_request_count @email = ?"
        elif counter_type == 'procurement':
            query = "EXEC dbo.sp_increment_procurement_count @email = ?"
        else:
            logger.warning(f"Unknown counter type: {counter_type}")
            return False
            
        success, error = execute_non_query_func(query, (email,))
        
        if error:
            logger.error(f"Error incrementing {counter_type} counter for {email}: {error}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Exception incrementing counter: {e}")
        return False


# ==============================================================================
# AUTOFILL UI COMPONENTS
# ==============================================================================

def render_email_lookup_widget(
    email_key: str = "email_lookup",
    label: str = "📧 Email Address *",
    execute_query_func = None
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Render email input field with profile lookup
    
    Args:
        email_key: Unique key for the widget
        label: Label for the email field
        execute_query_func: Function to execute database queries
        
    Returns:
        Tuple of (email, profile_dict or None)
    """
    col1, col2 = st.columns([3, 1])
    
    with col1:
        email = st.text_input(
            label,
            key=email_key,
            placeholder="user@vdh.virginia.gov",
            help="Enter your email to auto-fill your information"
        )
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        lookup_button = st.button("🔍 Lookup", key=f"{email_key}_lookup")
    
    profile = None
    
    # Check if email is in session state (from previous lookup)
    profile_key = f"{email_key}_profile"
    if profile_key in st.session_state:
        profile = st.session_state[profile_key]
    
    # Perform lookup if button clicked
    if lookup_button and email and execute_query_func:
        profile = get_user_profile_by_email(email, execute_query_func)
        
        if profile:
            st.session_state[profile_key] = profile
            st.success(f"✅ Found profile for {profile['full_name']}")
            st.info("📝 Your information has been auto-filled below. Please review and update if needed.")
        else:
            st.session_state[profile_key] = None
            st.info("👤 New user - please fill in your information below. We'll save it for next time!")
    
    return email, profile


def render_autofill_form_fields(
    profile: Optional[Dict[str, Any]] = None,
    name_key: str = "full_name",
    phone_key: str = "phone",
    department_key: str = "department",
    location_key: str = "location",
    show_department: bool = True,
    show_location: bool = True
) -> Dict[str, Any]:
    """
    Render form fields with autofill from profile
    
    Args:
        profile: User profile dictionary (optional)
        name_key: Key for name field
        phone_key: Key for phone field
        department_key: Key for department field
        location_key: Key for location field
        show_department: Whether to show department field
        show_location: Whether to show location field
        
    Returns:
        Dictionary with form values
    """
    form_values = {}
    
    # Name field (always show)
    default_name = profile.get('full_name', '') if profile else ''
    form_values['full_name'] = st.text_input(
        "👤 Full Name *",
        value=default_name,
        key=name_key,
        placeholder="John Doe"
    )
    
    # Phone field (always show)
    default_phone = profile.get('phone', '') if profile else ''
    form_values['phone'] = st.text_input(
        "📞 Phone Number *",
        value=default_phone,
        key=phone_key,
        placeholder="804-555-0100"
    )
    
    # Department field (conditional)
    if show_department:
        default_dept = profile.get('department', '') if profile else ''
        departments = [
            "", "IT", "Administration", "Nursing", "Environmental Health",
            "Vital Records", "Clinical Services", "Maintenance", "Other"
        ]
        dept_index = departments.index(default_dept) if default_dept in departments else 0
        form_values['department'] = st.selectbox(
            "🏢 Department *",
            departments,
            index=dept_index,
            key=department_key
        )
    
    # Location field (conditional)
    if show_location:
        default_loc = profile.get('location', '') if profile else ''
        locations = [
            "", "Petersburg", "Dinwiddie", "Sussex", "Surry",
            "Prince George", "Hopewell", "Greensville/Emporia"
        ]
        loc_index = locations.index(default_loc) if default_loc in locations else 0
        form_values['location'] = st.selectbox(
            "📍 Location *",
            locations,
            index=loc_index,
            key=location_key
        )
    
    return form_values


def render_profile_info_box(profile: Dict[str, Any]):
    """
    Display user profile information in an info box
    
    Args:
        profile: User profile dictionary
    """
    if not profile:
        return
    
    with st.expander("👤 Your Profile Information", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {profile.get('full_name', 'N/A')}")
            st.write(f"**Email:** {profile.get('email', 'N/A')}")
            st.write(f"**Phone:** {profile.get('phone', 'N/A')}")
        
        with col2:
            st.write(f"**Department:** {profile.get('department', 'N/A')}")
            st.write(f"**Location:** {profile.get('location', 'N/A')}")
            
            if profile.get('form_submissions_count', 0) > 0:
                st.write(f"**Form Submissions:** {profile['form_submissions_count']}")
        
        st.caption(f"Profile created: {profile.get('created_at', 'N/A')}")
        st.caption(f"Last updated: {profile.get('updated_at', 'N/A')}")


# ==============================================================================
# PROFILE MANAGEMENT UI
# ==============================================================================

def render_user_profile_manager(execute_query_func, execute_non_query_func):
    """
    Render user profile management interface
    
    Args:
        execute_query_func: Function to execute database queries
        execute_non_query_func: Function to execute database commands
    """
    st.title("👤 User Profile Management")
    
    st.info("""
    **User profiles** store your information for quick form filling. 
    When you submit any form (tickets, vehicle requests, procurement), your profile is automatically created or updated.
    """)
    
    # Profile lookup
    st.subheader("🔍 Find Your Profile")
    
    lookup_email = st.text_input(
        "Enter your email address",
        placeholder="your.email@vdh.virginia.gov",
        key="profile_mgmt_email"
    )
    
    if st.button("🔍 Search", key="search_profile"):
        if lookup_email:
            profile = get_user_profile_by_email(lookup_email, execute_query_func)
            
            if profile:
                st.success(f"✅ Profile found for {profile['full_name']}")
                
                # Display profile details
                st.markdown("---")
                st.subheader("📋 Profile Details")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("### Contact Information")
                    st.write(f"**Name:** {profile.get('full_name', 'N/A')}")
                    st.write(f"**Email:** {profile.get('email', 'N/A')}")
                    st.write(f"**Phone:** {profile.get('phone', 'N/A')}")
                    
                with col2:
                    st.write("### Work Information")
                    st.write(f"**Department:** {profile.get('department', 'N/A')}")
                    st.write(f"**Location:** {profile.get('location', 'N/A')}")
                    st.write(f"**Job Title:** {profile.get('job_title', 'N/A')}")
                
                # Usage statistics
                st.markdown("---")
                st.subheader("📊 Usage Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Submissions", profile.get('form_submissions_count', 0))
                with col2:
                    st.metric("Helpdesk Tickets", profile.get('ticket_count', 0))
                with col3:
                    st.metric("Vehicle Requests", profile.get('vehicle_request_count', 0))
                with col4:
                    st.metric("Procurement Requests", profile.get('procurement_request_count', 0))
                
                # Metadata
                st.markdown("---")
                st.caption(f"**Created:** {profile.get('created_at', 'N/A')}")
                st.caption(f"**Last Updated:** {profile.get('updated_at', 'N/A')}")
                st.caption(f"**Created From:** {profile.get('created_from_form', 'N/A')}")
                
                # Edit profile option
                st.markdown("---")
                if st.button("✏️ Edit Profile", key="edit_profile_btn"):
                    st.session_state['editing_profile'] = profile
                    st.rerun()
                    
            else:
                st.warning("❌ No profile found for this email address.")
                st.info("💡 Profiles are automatically created when you submit a form (helpdesk ticket, vehicle request, or procurement request).")
    
    # Edit profile if in edit mode
    if 'editing_profile' in st.session_state:
        profile = st.session_state['editing_profile']
        
        st.markdown("---")
        st.subheader("✏️ Edit Profile")
        
        with st.form("edit_profile_form"):
            updated_name = st.text_input("Full Name", value=profile.get('full_name', ''))
            updated_phone = st.text_input("Phone", value=profile.get('phone', ''))
            updated_dept = st.text_input("Department", value=profile.get('department', ''))
            updated_location = st.text_input("Location", value=profile.get('location', ''))
            updated_job_title = st.text_input("Job Title", value=profile.get('job_title', ''))
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Save Changes", use_container_width=True)
            with col2:
                cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if submit:
                # Update profile
                update_query = """
                    UPDATE dbo.user_profiles
                    SET full_name = ?, phone = ?, department = ?, 
                        location = ?, job_title = ?, updated_at = GETDATE()
                    WHERE email = ?
                """
                success, error = execute_non_query_func(
                    update_query,
                    (updated_name, updated_phone, updated_dept, updated_location, 
                     updated_job_title, profile['email'])
                )
                
                if success:
                    st.success("✅ Profile updated successfully!")
                    del st.session_state['editing_profile']
                    st.rerun()
                else:
                    st.error(f"❌ Error updating profile: {error}")
            
            if cancel:
                del st.session_state['editing_profile']
                st.rerun()


# ==============================================================================
# PROFILE STATISTICS
# ==============================================================================

def get_profile_statistics(execute_query_func) -> Dict[str, Any]:
    """
    Get overall user profile statistics
    
    Args:
        execute_query_func: Function to execute database queries
        
    Returns:
        Dictionary with statistics
    """
    try:
        query = """
            SELECT 
                COUNT(*) as total_profiles,
                SUM(ticket_count) as total_tickets,
                SUM(vehicle_request_count) as total_vehicle_requests,
                SUM(procurement_request_count) as total_procurement_requests,
                AVG(form_submissions_count) as avg_submissions_per_user
            FROM dbo.user_profiles
            WHERE is_active = 1
        """
        
        result_df, error = execute_query_func(query)
        
        if error or result_df is None or result_df.empty:
            return {}
            
        return result_df.iloc[0].to_dict()
        
    except Exception as e:
        logger.error(f"Error getting profile statistics: {e}")
        return {}
