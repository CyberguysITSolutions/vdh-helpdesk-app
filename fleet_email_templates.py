# ==============================================================================
# FLEET MANAGEMENT EMAIL TEMPLATES
# ==============================================================================
# Add this section to email_automation.py after the Procurement section

def email_vehicle_request_submitted(request_data: Dict[str, Any]) -> bool:
    """
    Send confirmation to requester and notification to fleet admin when vehicle is requested
    """
    
    request_url = f"{EmailConfig.APP_URL}/?vehicle_request_id={request_data.get('request_id')}"
    
    # Email to Requester (Confirmation)
    requester_body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">🚗 Vehicle Request Submitted</h2>
    
    <p>Hello {html.escape(request_data.get('requester_name', 'there'))},</p>
    
    <p>Your vehicle request has been successfully submitted and is awaiting fleet administrator approval.</p>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid {EmailConfig.VDH_ORANGE}; margin: 20px 0;">
        <p style="margin: 0;"><strong>Request Details:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Request ID:</strong> #{request_data.get('request_id')}</li>
            <li><strong>Vehicle:</strong> {html.escape(request_data.get('year', ''))} {html.escape(request_data.get('make_model', 'N/A'))}</li>
            <li><strong>License Plate:</strong> {html.escape(request_data.get('license_plate', 'N/A'))}</li>
            <li><strong>Start Date:</strong> {request_data.get('start_date', 'N/A')}</li>
            <li><strong>End Date:</strong> {request_data.get('end_date', 'N/A')}</li>
            <li><strong>Destination:</strong> {html.escape(request_data.get('destination', 'N/A'))}</li>
        </ul>
    </div>
    
    <div style="background-color: #d1ecf1; border: 1px solid #0066cc; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>📋 Next Steps:</strong></p>
        <ul style="margin: 0; padding-left: 20px;">
            <li>Fleet administrator will review your request</li>
            <li>You will receive email notification when approved or if any issues arise</li>
            <li>Average approval time: 1-2 business days</li>
            <li>Upon approval, you can pick up the vehicle on your start date</li>
        </ul>
    </div>
    
    {create_button('Track Request Status', request_url)}
    
    <p style="margin-top: 20px;"><strong>Important Reminders:</strong></p>
    <ul>
        <li>Bring your driver's license when picking up the vehicle</li>
        <li>Complete the vehicle inspection form before departing</li>
        <li>Log your trip in the system when you start and end your journey</li>
        <li>Return the vehicle with a full tank of gas</li>
    </ul>
    
    <p>Thank you for using VDH Fleet Services!</p>
    
    <p>Best regards,<br><strong>VDH Fleet Management</strong></p>
    """
    
    html_email_requester = wrap_email_template(requester_body, "Vehicle Request Submitted")
    
    # Send to requester
    success = send_email(
        to_addresses=[request_data.get('requester_email')],
        subject=f"Vehicle Request #{request_data.get('request_id')} - Awaiting Approval",
        html_body=html_email_requester,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )
    
    # Email to Fleet Admin (Notification)
    if success:
        duration_days = (datetime.strptime(request_data.get('end_date'), '%Y-%m-%d') - 
                        datetime.strptime(request_data.get('start_date'), '%Y-%m-%d')).days + 1
        
        admin_body = f"""
        <h2 style="color: {EmailConfig.VDH_NAVY};">🚗 New Vehicle Request Requires Approval</h2>
        
        <p>A new vehicle request has been submitted and requires your attention:</p>
        
        <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid {EmailConfig.VDH_ORANGE}; margin: 20px 0;">
            <p style="margin: 0;"><strong>Request Information:</strong></p>
            <ul style="margin: 10px 0;">
                <li><strong>Request ID:</strong> #{request_data.get('request_id')}</li>
                <li><strong>Requester:</strong> {html.escape(request_data.get('requester_name', 'N/A'))} ({request_data.get('requester_email', 'N/A')})</li>
                <li><strong>Phone:</strong> {html.escape(request_data.get('requester_phone', 'N/A'))}</li>
                <li><strong>Department:</strong> {html.escape(request_data.get('department', 'N/A'))}</li>
                <li><strong>Duration:</strong> {duration_days} day(s)</li>
            </ul>
        </div>
        
        <div style="background-color: white; border: 2px solid {EmailConfig.VDH_NAVY}; padding: 15px; margin: 20px 0; border-radius: 5px;">
            <p style="margin: 0;"><strong>🚗 Requested Vehicle:</strong></p>
            <h3 style="margin: 10px 0; color: {EmailConfig.VDH_NAVY};">{html.escape(request_data.get('year', ''))} {html.escape(request_data.get('make_model', 'N/A'))}</h3>
            <p style="margin: 0;">License Plate: <strong>{html.escape(request_data.get('license_plate', 'N/A'))}</strong></p>
            <p style="margin: 5px 0 0 0;">Current Mileage: <strong>{request_data.get('current_mileage', 'N/A'):,}</strong> miles</p>
        </div>
        
        <p><strong>Trip Details:</strong></p>
        <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; margin: 10px 0;">
            <p style="margin: 0;"><strong>Start Date:</strong> {request_data.get('start_date', 'N/A')}</p>
            <p style="margin: 5px 0;"><strong>End Date:</strong> {request_data.get('end_date', 'N/A')}</p>
            <p style="margin: 5px 0;"><strong>Destination:</strong> {html.escape(request_data.get('destination', 'N/A'))}</p>
            <p style="margin: 5px 0;"><strong>Estimated Miles:</strong> {request_data.get('estimated_miles', 'N/A')} miles</p>
        </div>
        
        <p><strong>Purpose of Trip:</strong></p>
        <div style="background-color: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
            {html.escape(request_data.get('purpose', 'No purpose provided'))}
        </div>
        
        {create_button('Review & Approve Request', request_url, EmailConfig.VDH_NAVY)}
        
        <p style="margin-top: 20px; font-size: 12px; color: #666;">
            Please review and approve/reject this request within 1 business day to ensure timely vehicle availability.
        </p>
        """
        
        html_email_admin = wrap_email_template(admin_body, "New Vehicle Request")
        
        fleet_admin_emails = os.getenv("FLEET_ADMIN_EMAILS", os.getenv("ADMIN_EMAILS", "gclarke@vdh.virginia.gov")).split(',')
        
        send_email(
            to_addresses=fleet_admin_emails,
            subject=f"[Action Required] Vehicle Request #{request_data.get('request_id')} - {request_data.get('make_model')}",
            html_body=html_email_admin,
            cc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
        )
    
    return success


def email_vehicle_request_approved(request_data: Dict[str, Any], approved_by: str) -> bool:
    """Notify requester that their vehicle request has been approved"""
    
    request_url = f"{EmailConfig.APP_URL}/?vehicle_request_id={request_data.get('request_id')}"
    
    body = f"""
    <h2 style="color: #28a745;">✅ Vehicle Request Approved!</h2>
    
    <p>Hello {html.escape(request_data.get('requester_name', 'there'))},</p>
    
    <p>Great news! Your vehicle request has been approved and is ready for pickup.</p>
    
    <div style="background-color: #d4edda; border: 1px solid #28a745; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p style="margin: 0 0 10px 0;"><strong>✅ Approved By:</strong> {html.escape(approved_by)}</p>
        <p style="margin: 0;"><strong>Approval Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    
    <div style="background-color: white; border: 2px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0;"><strong>🚗 Your Assigned Vehicle:</strong></p>
        <h3 style="margin: 10px 0; color: {EmailConfig.VDH_NAVY};">{html.escape(request_data.get('year', ''))} {html.escape(request_data.get('make_model', 'N/A'))}</h3>
        <p style="margin: 0;">License Plate: <strong>{html.escape(request_data.get('license_plate', 'N/A'))}</strong></p>
        <p style="margin: 5px 0 0 0;">Current Mileage: <strong>{request_data.get('current_mileage', 'N/A'):,}</strong> miles</p>
    </div>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; margin: 20px 0;">
        <p style="margin: 0;"><strong>📅 Reservation Period:</strong></p>
        <p style="margin: 10px 0 0 0;">
            <strong>Pickup Date:</strong> {request_data.get('start_date', 'N/A')}<br>
            <strong>Return Date:</strong> {request_data.get('end_date', 'N/A')}
        </p>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>📋 Pre-Departure Checklist:</strong></p>
        <ol style="margin: 0; padding-left: 20px;">
            <li><strong>Bring your driver's license</strong> for verification</li>
            <li><strong>Complete vehicle inspection form</strong> before departure</li>
            <li><strong>Check fuel level</strong> and tire condition</li>
            <li><strong>Log trip start</strong> in the VDH Fleet Management system</li>
            <li><strong>Take photos</strong> of any pre-existing damage</li>
            <li><strong>Emergency contact:</strong> 804.507.8404</li>
        </ol>
    </div>
    
    <div style="background-color: #d1ecf1; border: 1px solid #0066cc; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>🔐 Vehicle Location & Keys:</strong></p>
        <p style="margin: 0;">
            <strong>Pickup Location:</strong> VDH Crater Petersburg<br>
            <strong>Address:</strong> 301 Halifax St, Petersburg, VA 23803<br>
            <strong>Hours:</strong> Monday-Friday, 8:00 AM - 5:00 PM<br>
            <strong>Keys:</strong> Available at fleet office - see receptionist
        </p>
    </div>
    
    {create_button('View Request Details', request_url)}
    
    <div style="background-color: #f8d7da; border: 1px solid #dc3545; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>⚠️ Important Return Instructions:</strong></p>
        <ul style="margin: 0; padding-left: 20px;">
            <li>Return vehicle with <strong>full tank of gas</strong></li>
            <li>Log trip completion in system with final mileage</li>
            <li>Clean interior and remove all personal items</li>
            <li>Report any damage or mechanical issues immediately</li>
            <li>Return keys to fleet office</li>
        </ul>
    </div>
    
    <p>Have a safe trip!</p>
    
    <p>Best regards,<br><strong>VDH Fleet Management Team</strong></p>
    """
    
    html_email = wrap_email_template(body, "Vehicle Request Approved")
    
    return send_email(
        to_addresses=[request_data.get('requester_email')],
        subject=f"✅ Vehicle Request #{request_data.get('request_id')} - Approved & Ready for Pickup!",
        html_body=html_email,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )


def email_vehicle_request_rejected(request_data: Dict[str, Any], rejected_by: str, rejection_reason: str) -> bool:
    """Notify requester that their vehicle request has been rejected"""
    
    request_url = f"{EmailConfig.APP_URL}/?vehicle_request_id={request_data.get('request_id')}"
    
    body = f"""
    <h2 style="color: #dc3545;">Vehicle Request - Unable to Approve</h2>
    
    <p>Hello {html.escape(request_data.get('requester_name', 'there'))},</p>
    
    <p>We regret to inform you that your vehicle request could not be approved at this time.</p>
    
    <div style="background-color: #f8d7da; border: 1px solid #dc3545; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p style="margin: 0 0 10px 0;"><strong>Reviewed By:</strong> {html.escape(rejected_by)}</p>
        <p style="margin: 0;"><strong>Review Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid #dc3545; margin: 20px 0;">
        <p style="margin: 0;"><strong>Request Details:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Request ID:</strong> #{request_data.get('request_id')}</li>
            <li><strong>Vehicle:</strong> {html.escape(request_data.get('year', ''))} {html.escape(request_data.get('make_model', 'N/A'))}</li>
            <li><strong>Dates:</strong> {request_data.get('start_date', 'N/A')} to {request_data.get('end_date', 'N/A')}</li>
        </ul>
    </div>
    
    <p><strong>Reason:</strong></p>
    <div style="background-color: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
        {html.escape(rejection_reason)}
    </div>
    
    <div style="background-color: #d1ecf1; border: 1px solid #0066cc; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>💡 Alternative Options:</strong></p>
        <ul style="margin: 0; padding-left: 20px;">
            <li>Check alternative dates when the vehicle may be available</li>
            <li>Browse other available vehicles in the fleet</li>
            <li>Contact fleet management for personalized assistance</li>
            <li>Submit a new request with adjusted parameters</li>
        </ul>
    </div>
    
    {create_button('Browse Available Vehicles', f"{EmailConfig.APP_URL}/?public=vehicle_request")}
    
    <p style="margin-top: 20px;">If you have questions about this decision or need assistance with alternative arrangements, please contact:</p>
    <p>📧 {EmailConfig.SERVICE_EMAIL}<br>
    📞 804.507.8404</p>
    
    <p>Thank you for your understanding.</p>
    
    <p>Best regards,<br><strong>VDH Fleet Management Team</strong></p>
    """
    
    html_email = wrap_email_template(body, "Vehicle Request Update")
    
    return send_email(
        to_addresses=[request_data.get('requester_email')],
        subject=f"Vehicle Request #{request_data.get('request_id')} - Update Required",
        html_body=html_email,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )


def email_vehicle_unavailable(request_data: Dict[str, Any], reason: str = "maintenance") -> bool:
    """Notify requester when their approved vehicle becomes unavailable"""
    
    reasons_map = {
        "maintenance": {
            "title": "Vehicle Requires Maintenance",
            "icon": "🔧",
            "explanation": "The vehicle you requested requires unexpected maintenance and will not be available for your reservation period."
        },
        "accident": {
            "title": "Vehicle Temporarily Out of Service",
            "icon": "⚠️",
            "explanation": "The vehicle you requested has been involved in an incident and is temporarily unavailable."
        },
        "already_dispatched": {
            "title": "Vehicle Already in Use",
            "icon": "🚗",
            "explanation": "The vehicle you requested has been dispatched for another priority assignment."
        }
    }
    
    reason_info = reasons_map.get(reason, reasons_map["maintenance"])
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_ORANGE};">{reason_info['icon']} {reason_info['title']}</h2>
    
    <p>Hello {html.escape(request_data.get('requester_name', 'there'))},</p>
    
    <p>We need to inform you of an important change to your vehicle reservation.</p>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p style="margin: 0 0 10px 0;"><strong>⚠️ Status Update:</strong></p>
        <p style="margin: 0;">{reason_info['explanation']}</p>
    </div>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; margin: 20px 0;">
        <p style="margin: 0;"><strong>Your Reservation:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Request ID:</strong> #{request_data.get('request_id')}</li>
            <li><strong>Original Vehicle:</strong> {html.escape(request_data.get('year', ''))} {html.escape(request_data.get('make_model', 'N/A'))}</li>
            <li><strong>Dates:</strong> {request_data.get('start_date', 'N/A')} to {request_data.get('end_date', 'N/A')}</li>
        </ul>
    </div>
    
    <div style="background-color: #d1ecf1; border: 1px solid #0066cc; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>💡 Next Steps:</strong></p>
        <p style="margin: 0;">
            Our fleet team is working to secure an alternative vehicle for you. 
            We will contact you within <strong>24 hours</strong> with:
        </p>
        <ul style="margin: 10px 0;">
            <li>A comparable replacement vehicle, or</li>
            <li>Alternative scheduling options, or</li>
            <li>Further assistance with your transportation needs</li>
        </ul>
    </div>
    
    {create_button('View Available Vehicles', f"{EmailConfig.APP_URL}/?public=vehicle_request")}
    
    <p style="margin-top: 20px;">We sincerely apologize for this inconvenience. If you need immediate assistance or have urgent transportation needs, please contact us right away:</p>
    
    <p>📧 {EmailConfig.SERVICE_EMAIL}<br>
    📞 804.507.8404</p>
    
    <p>Thank you for your patience and understanding.</p>
    
    <p>Best regards,<br><strong>VDH Fleet Management Team</strong></p>
    """
    
    html_email = wrap_email_template(body, "Vehicle Reservation Update")
    
    # Notify requester
    success = send_email(
        to_addresses=[request_data.get('requester_email')],
        subject=f"⚠️ Important: Vehicle Reservation #{request_data.get('request_id')} - Update Required",
        html_body=html_email,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )
    
    # Also alert fleet admins
    if success:
        admin_body = f"""
        <h2 style="color: {EmailConfig.VDH_ORANGE};">⚠️ Vehicle Unavailable - Driver Notified</h2>
        
        <p>A vehicle reservation has been marked as unavailable. The driver has been notified.</p>
        
        <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; margin: 20px 0;">
            <p style="margin: 0;"><strong>Affected Reservation:</strong></p>
            <ul style="margin: 10px 0;">
                <li><strong>Request ID:</strong> #{request_data.get('request_id')}</li>
                <li><strong>Driver:</strong> {html.escape(request_data.get('requester_name', 'N/A'))}</li>
                <li><strong>Vehicle:</strong> {html.escape(request_data.get('make_model', 'N/A'))}</li>
                <li><strong>Reason:</strong> {reason_info['title']}</li>
            </ul>
        </div>
        
        <p><strong>⚡ Action Required:</strong> Contact driver within 24 hours with alternative vehicle or rescheduling options.</p>
        """
        
        fleet_admin_emails = os.getenv("FLEET_ADMIN_EMAILS", os.getenv("ADMIN_EMAILS", "gclarke@vdh.virginia.gov")).split(',')
        send_email(
            to_addresses=fleet_admin_emails,
            subject=f"[Urgent] Vehicle Reservation #{request_data.get('request_id')} - Alternative Needed",
            html_body=wrap_email_template(admin_body, "Vehicle Unavailable Alert"),
            cc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
        )
    
    return success


def email_trip_started(trip_data: Dict[str, Any]) -> bool:
    """Notify fleet admin when a trip is started"""
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">🚗 Trip Started - Vehicle Dispatched</h2>
    
    <p>A vehicle has been dispatched for a new trip:</p>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid {EmailConfig.VDH_ORANGE}; margin: 20px 0;">
        <p style="margin: 0;"><strong>Trip Information:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Trip ID:</strong> #{trip_data.get('trip_id')}</li>
            <li><strong>Driver:</strong> {html.escape(trip_data.get('driver_name', 'N/A'))} ({trip_data.get('driver_email', 'N/A')})</li>
            <li><strong>Department:</strong> {html.escape(trip_data.get('department', 'N/A'))}</li>
            <li><strong>Start Time:</strong> {trip_data.get('start_datetime', datetime.now().strftime('%Y-%m-%d %H:%M'))}</li>
        </ul>
    </div>
    
    <div style="background-color: white; border: 2px solid {EmailConfig.VDH_NAVY}; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0;"><strong>🚗 Vehicle:</strong></p>
        <p style="margin: 10px 0 0 0;">
            <strong>{html.escape(trip_data.get('make_model', 'N/A'))}</strong><br>
            License: {html.escape(trip_data.get('license_plate', 'N/A'))}<br>
            Starting Mileage: <strong>{trip_data.get('start_mileage', 0):,}</strong> miles
        </p>
    </div>
    
    <p><strong>Trip Details:</strong></p>
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; margin: 10px 0;">
        <p style="margin: 0;"><strong>From:</strong> {html.escape(trip_data.get('start_location', 'N/A'))}</p>
        <p style="margin: 5px 0 0 0;"><strong>Notes:</strong> {html.escape(trip_data.get('notes', 'No notes provided'))}</p>
    </div>
    
    <p style="margin-top: 20px; font-size: 12px; color: #666;">
        This is an automated notification for fleet tracking purposes. No action required unless the trip exceeds expected duration.
    </p>
    """
    
    html_email = wrap_email_template(body, "Trip Started Notification")
    
    fleet_admin_emails = os.getenv("FLEET_ADMIN_EMAILS", os.getenv("ADMIN_EMAILS", "gclarke@vdh.virginia.gov")).split(',')
    
    return send_email(
        to_addresses=fleet_admin_emails,
        subject=f"🚗 Trip Started - {trip_data.get('make_model')} ({trip_data.get('license_plate')})",
        html_body=html_email,
        cc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL],
        use_notifications_account=True
    )


def email_trip_completed(trip_data: Dict[str, Any]) -> bool:
    """Send trip summary to driver and fleet admin when trip is completed"""
    
    miles_driven = trip_data.get('end_mileage', 0) - trip_data.get('start_mileage', 0)
    
    # Calculate trip duration
    start_time = datetime.strptime(trip_data.get('start_datetime'), '%Y-%m-%d %H:%M:%S') if trip_data.get('start_datetime') else datetime.now()
    end_time = datetime.strptime(trip_data.get('end_datetime'), '%Y-%m-%d %H:%M:%S') if trip_data.get('end_datetime') else datetime.now()
    duration = end_time - start_time
    hours = duration.total_seconds() / 3600
    
    # Email to Driver
    driver_body = f"""
    <h2 style="color: #28a745;">🏁 Trip Completed - Thank You!</h2>
    
    <p>Hello {html.escape(trip_data.get('driver_name', 'there'))},</p>
    
    <p>Thank you for using VDH Fleet Services. Your trip has been successfully logged and the vehicle has been returned.</p>
    
    <div style="background-color: #d4edda; border: 1px solid #28a745; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p style="margin: 0;"><strong>✅ Trip Summary</strong></p>
        <p style="margin: 10px 0 0 0;">Trip ID: <strong>#{trip_data.get('trip_id')}</strong></p>
    </div>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; margin: 20px 0;">
        <p style="margin: 0;"><strong>🚗 Vehicle:</strong></p>
        <p style="margin: 10px 0 0 0;">
            <strong>{html.escape(trip_data.get('make_model', 'N/A'))}</strong><br>
            License Plate: {html.escape(trip_data.get('license_plate', 'N/A'))}
        </p>
    </div>
    
    <div style="background-color: white; border: 2px solid {EmailConfig.VDH_NAVY}; padding: 20px; margin: 20px 0; border-radius: 5px;">
        <h3 style="margin: 0 0 15px 0; color: {EmailConfig.VDH_NAVY}; text-align: center;">📊 Trip Statistics</h3>
        
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px; font-weight: bold;">Start Location:</td>
                <td style="padding: 10px;">{html.escape(trip_data.get('start_location', 'N/A'))}</td>
            </tr>
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px; font-weight: bold;">End Location:</td>
                <td style="padding: 10px;">{html.escape(trip_data.get('end_location', 'N/A'))}</td>
            </tr>
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px; font-weight: bold;">Start Mileage:</td>
                <td style="padding: 10px;">{trip_data.get('start_mileage', 0):,} miles</td>
            </tr>
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px; font-weight: bold;">End Mileage:</td>
                <td style="padding: 10px;">{trip_data.get('end_mileage', 0):,} miles</td>
            </tr>
            <tr style="border-bottom: 1px solid #ddd; background-color: {EmailConfig.VDH_LIGHT_GRAY};">
                <td style="padding: 10px; font-weight: bold;">Miles Driven:</td>
                <td style="padding: 10px; font-weight: bold; color: {EmailConfig.VDH_ORANGE};">{miles_driven:,} miles</td>
            </tr>
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px; font-weight: bold;">Trip Duration:</td>
                <td style="padding: 10px;">{hours:.1f} hours</td>
            </tr>
            <tr>
                <td style="padding: 10px; font-weight: bold;">Return Date:</td>
                <td style="padding: 10px;">{trip_data.get('end_datetime', 'N/A')}</td>
            </tr>
        </table>
    </div>
    
    <div style="background-color: #d1ecf1; border: 1px solid #0066cc; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>📋 Post-Trip Reminders:</strong></p>
        <ul style="margin: 0; padding-left: 20px;">
            <li>Ensure the vehicle was returned with a full tank</li>
            <li>All personal items have been removed</li>
            <li>Vehicle keys returned to fleet office</li>
            <li>Any damage reported to fleet management</li>
        </ul>
    </div>
    
    <p>If you noticed any issues with the vehicle during your trip, please report them to fleet management as soon as possible.</p>
    
    <p>Thank you for using VDH Fleet Services responsibly!</p>
    
    <p>Best regards,<br><strong>VDH Fleet Management Team</strong></p>
    """
    
    html_email_driver = wrap_email_template(driver_body, "Trip Completed")
    
    # Send to driver
    success = send_email(
        to_addresses=[trip_data.get('driver_email')],
        subject=f"🏁 Trip Completed - {trip_data.get('make_model')} - {miles_driven} miles",
        html_body=html_email_driver,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )
    
    # Email to Fleet Admin
    if success:
        admin_body = f"""
        <h2 style="color: {EmailConfig.VDH_NAVY};">🏁 Trip Completed - Vehicle Returned</h2>
        
        <p>A vehicle has been returned and the trip has been completed:</p>
        
        <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
            <p style="margin: 0;"><strong>Trip Summary:</strong></p>
            <ul style="margin: 10px 0;">
                <li><strong>Trip ID:</strong> #{trip_data.get('trip_id')}</li>
                <li><strong>Driver:</strong> {html.escape(trip_data.get('driver_name', 'N/A'))} ({trip_data.get('driver_email', 'N/A')})</li>
                <li><strong>Department:</strong> {html.escape(trip_data.get('department', 'N/A'))}</li>
                <li><strong>Duration:</strong> {hours:.1f} hours</li>
            </ul>
        </div>
        
        <div style="background-color: white; border: 2px solid {EmailConfig.VDH_NAVY}; padding: 15px; margin: 20px 0; border-radius: 5px;">
            <p style="margin: 0;"><strong>🚗 Vehicle:</strong></p>
            <p style="margin: 10px 0 0 0;">
                <strong>{html.escape(trip_data.get('make_model', 'N/A'))}</strong><br>
                License: {html.escape(trip_data.get('license_plate', 'N/A'))}<br>
                <strong>Miles Driven:</strong> <span style="color: {EmailConfig.VDH_ORANGE}; font-weight: bold;">{miles_driven:,} miles</span><br>
                <strong>New Mileage:</strong> {trip_data.get('end_mileage', 0):,} miles
            </p>
        </div>
        
        <p><strong>Route:</strong></p>
        <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; margin: 10px 0;">
            <p style="margin: 0;">From: <strong>{html.escape(trip_data.get('start_location', 'N/A'))}</strong></p>
            <p style="margin: 5px 0 0 0;">To: <strong>{html.escape(trip_data.get('end_location', 'N/A'))}</strong></p>
        </div>
        
        <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px;">
            <p style="margin: 0 0 10px 0;"><strong>⚠️ Post-Return Checklist:</strong></p>
            <ul style="margin: 0; padding-left: 20px;">
                <li>Verify vehicle fuel level</li>
                <li>Inspect for new damage</li>
                <li>Check interior cleanliness</li>
                <li>Update vehicle status in system</li>
                <li>Schedule service if needed</li>
            </ul>
        </div>
        
        <p style="margin-top: 20px; font-size: 12px; color: #666;">
            Vehicle status has been automatically updated to "Available" in the fleet management system.
        </p>
        """
        
        html_email_admin = wrap_email_template(admin_body, "Vehicle Returned")
        
        fleet_admin_emails = os.getenv("FLEET_ADMIN_EMAILS", os.getenv("ADMIN_EMAILS", "gclarke@vdh.virginia.gov")).split(',')
        
        send_email(
            to_addresses=fleet_admin_emails,
            subject=f"🏁 Vehicle Returned - {trip_data.get('make_model')} - {miles_driven} miles driven",
            html_body=html_email_admin,
            cc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
        )
    
    return success


def email_vehicle_service_needed(vehicle_data: Dict[str, Any], urgency: str = "due_soon") -> bool:
    """Alert fleet admin that a vehicle needs service"""
    
    miles_until_service = vehicle_data.get('miles_until_service', 0)
    current_mileage = vehicle_data.get('current_mileage', 0)
    
    urgency_config = {
        "overdue": {
            "color": "#dc3545",
            "icon": "🔴",
            "title": "URGENT: Vehicle Service OVERDUE",
            "priority": "CRITICAL",
            "action": "Remove from service immediately and schedule maintenance"
        },
        "due_now": {
            "color": "#fd7e14",
            "icon": "🟠",
            "title": "Vehicle Service Due NOW",
            "priority": "HIGH",
            "action": "Schedule service within 24 hours"
        },
        "due_soon": {
            "color": "#ffc107",
            "icon": "🟡",
            "title": "Vehicle Service Due Soon",
            "priority": "MEDIUM",
            "action": "Schedule service within 1 week"
        }
    }
    
    config = urgency_config.get(urgency, urgency_config["due_soon"])
    
    body = f"""
    <h2 style="color: {config['color']};">{config['icon']} {config['title']}</h2>
    
    <p>The following vehicle requires maintenance attention:</p>
    
    <div style="background-color: {config['color']}20; border: 2px solid {config['color']}; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p style="margin: 0; text-align: center;">
            <strong style="font-size: 18px; color: {config['color']};">PRIORITY: {config['priority']}</strong>
        </p>
    </div>
    
    <div style="background-color: white; border: 2px solid {EmailConfig.VDH_NAVY}; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0;"><strong>🚗 Vehicle Information:</strong></p>
        <h3 style="margin: 10px 0; color: {EmailConfig.VDH_NAVY};">{html.escape(vehicle_data.get('year', ''))} {html.escape(vehicle_data.get('make_model', 'N/A'))}</h3>
        <p style="margin: 0;">
            <strong>License Plate:</strong> {html.escape(vehicle_data.get('license_plate', 'N/A'))}<br>
            <strong>Current Mileage:</strong> {current_mileage:,} miles<br>
            <strong>Miles Until Service:</strong> <span style="color: {config['color']}; font-weight: bold;">{miles_until_service} miles</span>
        </p>
    </div>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; margin: 20px 0;">
        <p style="margin: 0;"><strong>Service History:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Last Service Date:</strong> {vehicle_data.get('last_service_date', 'N/A')}</li>
            <li><strong>Last Service Mileage:</strong> {vehicle_data.get('last_service_mileage', 0):,} miles</li>
            <li><strong>Miles Since Service:</strong> {current_mileage - vehicle_data.get('last_service_mileage', 0):,} miles</li>
            <li><strong>Service Interval:</strong> Every 3,000 miles</li>
        </ul>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>⚡ Required Action:</strong></p>
        <p style="margin: 0; font-size: 16px; font-weight: bold;">{config['action']}</p>
    </div>
    
    <div style="background-color: #d1ecf1; border: 1px solid #0066cc; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>📋 Service Checklist:</strong></p>
        <ul style="margin: 0; padding-left: 20px;">
            <li>Oil change and filter replacement</li>
            <li>Tire rotation and pressure check</li>
            <li>Brake inspection</li>
            <li>Fluid levels (coolant, brake, transmission)</li>
            <li>Battery test</li>
            <li>Multi-point safety inspection</li>
        </ul>
    </div>
    
    {create_button('View Vehicle Details', f"{EmailConfig.APP_URL}/?vehicle_id={vehicle_data.get('id')}")}
    
    <p style="margin-top: 20px;"><strong>Recommended Service Center:</strong></p>
    <p style="margin: 0;">
        VDH Crater Fleet Services<br>
        301 Halifax St<br>
        Petersburg, VA 23803<br>
        📞 804.507.8404
    </p>
    
    <p style="margin-top: 20px; font-size: 12px; color: #666;">
        This is an automated alert based on the vehicle's mileage tracking. 
        Please update the system after service is completed.
    </p>
    """
    
    html_email = wrap_email_template(body, "Vehicle Service Alert")
    
    fleet_admin_emails = os.getenv("FLEET_ADMIN_EMAILS", os.getenv("ADMIN_EMAILS", "gclarke@vdh.virginia.gov")).split(',')
    
    return send_email(
        to_addresses=fleet_admin_emails,
        subject=f"[{config['priority']}] {config['icon']} Vehicle Service - {vehicle_data.get('make_model')} ({vehicle_data.get('license_plate')})",
        html_body=html_email,
        cc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )


def email_vehicle_idle_alert(vehicle_data: Dict[str, Any], days_idle: int) -> bool:
    """Alert fleet admin about underutilized vehicles"""
    
    last_used = vehicle_data.get('last_used_date', 'Never')
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_ORANGE};">📊 Vehicle Utilization Alert</h2>
    
    <p>The following vehicle has not been used recently and may be underutilized:</p>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p style="margin: 0; text-align: center;">
            <strong style="font-size: 24px; color: {EmailConfig.VDH_ORANGE};">{days_idle} Days Idle</strong>
        </p>
    </div>
    
    <div style="background-color: white; border: 2px solid {EmailConfig.VDH_NAVY}; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0;"><strong>🚗 Vehicle Information:</strong></p>
        <h3 style="margin: 10px 0; color: {EmailConfig.VDH_NAVY};">{html.escape(vehicle_data.get('year', ''))} {html.escape(vehicle_data.get('make_model', 'N/A'))}</h3>
        <p style="margin: 0;">
            <strong>License Plate:</strong> {html.escape(vehicle_data.get('license_plate', 'N/A'))}<br>
            <strong>Current Status:</strong> {html.escape(vehicle_data.get('status', 'Available'))}<br>
            <strong>Current Mileage:</strong> {vehicle_data.get('current_mileage', 0):,} miles
        </p>
    </div>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; margin: 20px 0;">
        <p style="margin: 0;"><strong>📅 Usage Statistics:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Last Used Date:</strong> {last_used}</li>
            <li><strong>Days Since Last Use:</strong> <span style="color: {EmailConfig.VDH_ORANGE}; font-weight: bold;">{days_idle} days</span></li>
            <li><strong>Total Usage Count:</strong> {vehicle_data.get('usage_count', 0)} trips</li>
            <li><strong>Current Driver:</strong> {vehicle_data.get('current_driver', 'None')}</li>
        </ul>
    </div>
    
    <div style="background-color: #d1ecf1; border: 1px solid #0066cc; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>💡 Recommended Actions:</strong></p>
        <ul style="margin: 0; padding-left: 20px;">
            <li><strong>Review utilization:</strong> Is this vehicle still needed in the fleet?</li>
            <li><strong>Promote availability:</strong> Inform staff about this vehicle</li>
            <li><strong>Schedule maintenance:</strong> Even unused vehicles need periodic service</li>
            <li><strong>Test drive:</strong> Ensure vehicle is in good working condition</li>
            <li><strong>Battery maintenance:</strong> Check battery charge (start vehicle weekly)</li>
            <li><strong>Consider rotation:</strong> Evaluate if vehicle should be reassigned or sold</li>
        </ul>
    </div>
    
    {create_button('View Vehicle Details', f"{EmailConfig.APP_URL}/?vehicle_id={vehicle_data.get('id')}")}
    
    <div style="background-color: #f8d7da; border: 1px solid #dc3545; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>⚠️ Extended Inactivity Concerns:</strong></p>
        <ul style="margin: 0; padding-left: 20px;">
            <li>Battery degradation from extended non-use</li>
            <li>Tire flat spots from sitting</li>
            <li>Fuel system issues from old fuel</li>
            <li>Brake rotor rust and corrosion</li>
            <li>Fluid deterioration</li>
        </ul>
    </div>
    
    <p style="margin-top: 20px; font-size: 12px; color: #666;">
        Fleet vehicles should be used at least once every 30 days to maintain optimal condition. 
        This alert is generated for vehicles idle 45+ days.
    </p>
    """
    
    html_email = wrap_email_template(body, "Vehicle Utilization Alert")
    
    fleet_admin_emails = os.getenv("FLEET_ADMIN_EMAILS", os.getenv("ADMIN_EMAILS", "gclarke@vdh.virginia.gov")).split(',')
    
    return send_email(
        to_addresses=fleet_admin_emails,
        subject=f"📊 Vehicle Idle {days_idle} Days - {vehicle_data.get('make_model')} ({vehicle_data.get('license_plate')})",
        html_body=html_email,
        cc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL],
        use_notifications_account=True
    )


def email_weekly_fleet_summary(summary_data: Dict[str, Any]) -> bool:
    """Send weekly fleet utilization summary to fleet admin"""
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">📊 Weekly Fleet Management Summary</h2>
    
    <p>Here's your weekly fleet activity summary for the week of {summary_data.get('week_start', 'N/A')} to {summary_data.get('week_end', 'N/A')}:</p>
    
    <div style="display: flex; justify-content: space-around; margin: 20px 0; flex-wrap: wrap;">
        <div style="background-color: #d1ecf1; padding: 15px; border-radius: 5px; text-align: center; min-width: 150px; margin: 5px;">
            <h3 style="margin: 0; color: {EmailConfig.VDH_NAVY};">{summary_data.get('total_trips', 0)}</h3>
            <p style="margin: 5px 0 0 0; font-size: 14px;">Total Trips</p>
        </div>
        <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; text-align: center; min-width: 150px; margin: 5px;">
            <h3 style="margin: 0; color: {EmailConfig.VDH_NAVY};">{summary_data.get('miles_driven', 0):,}</h3>
            <p style="margin: 5px 0 0 0; font-size: 14px;">Miles Driven</p>
        </div>
        <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; text-align: center; min-width: 150px; margin: 5px;">
            <h3 style="margin: 0; color: {EmailConfig.VDH_NAVY};">{summary_data.get('pending_requests', 0)}</h3>
            <p style="margin: 5px 0 0 0; font-size: 14px;">Pending Requests</p>
        </div>
        <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; text-align: center; min-width: 150px; margin: 5px;">
            <h3 style="margin: 0; color: {EmailConfig.VDH_NAVY};">{summary_data.get('service_needed', 0)}</h3>
            <p style="margin: 5px 0 0 0; font-size: 14px;">Service Needed</p>
        </div>
    </div>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; margin: 20px 0;">
        <p style="margin: 0;"><strong>🚗 Fleet Status:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Available Vehicles:</strong> {summary_data.get('available_vehicles', 0)}</li>
            <li><strong>Dispatched Vehicles:</strong> {summary_data.get('dispatched_vehicles', 0)}</li>
            <li><strong>In Maintenance:</strong> {summary_data.get('maintenance_vehicles', 0)}</li>
            <li><strong>Out of Service:</strong> {summary_data.get('oos_vehicles', 0)}</li>
        </ul>
    </div>
    
    <h3 style="color: {EmailConfig.VDH_NAVY};">📈 Top 5 Most Used Vehicles</h3>
    <div style="background-color: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
        <ol style="margin: 0; padding-left: 20px;">
    """
    
    for vehicle in summary_data.get('top_vehicles', [])[:5]:
        body += f"<li>{vehicle.get('make_model')} ({vehicle.get('license_plate')}) - {vehicle.get('trips', 0)} trips, {vehicle.get('miles', 0):,} miles</li>"
    
    body += """
        </ol>
    </div>
    
    <h3 style="color: {EmailConfig.VDH_ORANGE};">⚠️ Attention Required</h3>
    """
    
    if summary_data.get('service_needed', 0) > 0:
        body += f"""
        <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 5px;">
            <p style="margin: 0;"><strong>🔧 {summary_data.get('service_needed', 0)} Vehicle(s) Need Service</strong></p>
            <p style="margin: 10px 0 0 0; font-size: 14px;">Review and schedule maintenance for optimal fleet health.</p>
        </div>
        """
    
    if summary_data.get('idle_vehicles', 0) > 0:
        body += f"""
        <div style="background-color: #d1ecf1; border: 1px solid #0066cc; padding: 15px; margin: 10px 0; border-radius: 5px;">
            <p style="margin: 0;"><strong>📊 {summary_data.get('idle_vehicles', 0)} Vehicle(s) Idle 45+ Days</strong></p>
            <p style="margin: 10px 0 0 0; font-size: 14px;">Consider utilization review or routine test drives.</p>
        </div>
        """
    
    if summary_data.get('pending_requests', 0) > 0:
        body += f"""
        <div style="background-color: #f8d7da; border: 1px solid #dc3545; padding: 15px; margin: 10px 0; border-radius: 5px;">
            <p style="margin: 0;"><strong>⏰ {summary_data.get('pending_requests', 0)} Pending Request(s)</strong></p>
            <p style="margin: 10px 0 0 0; font-size: 14px;">Review and respond to vehicle requests within 24 hours.</p>
        </div>
        """
    
    body += f"""
    {create_button('View Fleet Dashboard', EmailConfig.APP_URL)}
    
    <p style="margin-top: 20px;">Have a productive week ahead!</p>
    
    <p>Best regards,<br><strong>VDH Fleet Management System</strong></p>
    """
    
    html_email = wrap_email_template(body, "Weekly Fleet Summary")
    
    fleet_admin_emails = os.getenv("FLEET_ADMIN_EMAILS", os.getenv("ADMIN_EMAILS", "gclarke@vdh.virginia.gov")).split(',')
    
    return send_email(
        to_addresses=fleet_admin_emails,
        subject=f"📊 Weekly Fleet Summary - Week of {summary_data.get('week_start', 'N/A')}",
        html_body=html_email,
        use_notifications_account=True
    )
