"""
VDH Crater Service Center - Email Automation Module
====================================================

This module provides comprehensive email automation for the VDH Helpdesk application
using Office 365 SMTP with professional HTML email templates.

Email Accounts:
- service@craterservicecenter.com (Primary service notifications)
- notifications@craterservicecenter.com (Shared inbox for all system notifications)

Author: Cyber Guys DMV
Date: March 2026
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import html

logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

class EmailConfig:
    """Email configuration for O365 SMTP"""
    
    # O365 SMTP Settings
    SMTP_SERVER = "smtp.office365.com"
    SMTP_PORT = 587
    USE_TLS = True
    
    # Email Accounts
    SERVICE_EMAIL = "service@craterservicecenter.com"
    NOTIFICATIONS_EMAIL = "notifications@craterservicecenter.com"
    
    # Get credentials from environment variables (set in Azure App Service)
    SERVICE_PASSWORD = os.getenv("SERVICE_EMAIL_PASSWORD")
    NOTIFICATIONS_PASSWORD = os.getenv("NOTIFICATIONS_EMAIL_PASSWORD")
    
    # Application Settings
    APP_NAME = "VDH Crater Service Center"
    APP_URL = "https://vdh-helpdesk-app.azurewebsites.net"
    SUPPORT_PHONE = "804.507.8404"
    
    # VDH Branding Colors
    VDH_NAVY = "#002855"
    VDH_ORANGE = "#FF6B35"
    VDH_LIGHT_GRAY = "#F5F5F5"


# ==============================================================================
# HTML EMAIL TEMPLATES
# ==============================================================================

def get_email_header():
    """Standard email header with VDH branding"""
    return f"""
    <div style="background-color: {EmailConfig.VDH_NAVY}; padding: 20px; text-align: center;">
        <h1 style="color: white; margin: 0; font-family: Arial, sans-serif;">
            🏥 {EmailConfig.APP_NAME}
        </h1>
        <p style="color: {EmailConfig.VDH_ORANGE}; margin: 5px 0 0 0; font-size: 14px;">
            Virginia Department of Health
        </p>
    </div>
    """

def get_email_footer():
    """Standard email footer"""
    return f"""
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 20px; margin-top: 30px; border-top: 3px solid {EmailConfig.VDH_ORANGE};">
        <p style="margin: 0; font-size: 12px; color: #666;">
            <strong>{EmailConfig.APP_NAME}</strong><br>
            Virginia Department of Health - Crater Health District<br>
            📞 {EmailConfig.SUPPORT_PHONE} | 📧 {EmailConfig.SERVICE_EMAIL}<br>
            🌐 <a href="{EmailConfig.APP_URL}" style="color: {EmailConfig.VDH_NAVY};">{EmailConfig.APP_URL}</a>
        </p>
        <p style="margin: 10px 0 0 0; font-size: 11px; color: #999;">
            This is an automated message from the VDH Crater Service Center. Please do not reply directly to this email.
            For assistance, please contact {EmailConfig.SERVICE_EMAIL} or submit a ticket through the helpdesk portal.
        </p>
    </div>
    """

def create_button(text, url, color=None):
    """Create a styled button for emails"""
    if color is None:
        color = EmailConfig.VDH_ORANGE
    return f"""
    <a href="{url}" style="
        display: inline-block;
        background-color: {color};
        color: white;
        padding: 12px 30px;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        margin: 10px 0;
    ">{text}</a>
    """

def wrap_email_template(body_content, title="Notification"):
    """Wrap content in standard email template"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{html.escape(title)}</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4;">
            <tr>
                <td align="center" style="padding: 20px;">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <tr>
                            <td>
                                {get_email_header()}
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 30px;">
                                {body_content}
                            </td>
                        </tr>
                        <tr>
                            <td>
                                {get_email_footer()}
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


# ==============================================================================
# CORE EMAIL SENDING FUNCTION
# ==============================================================================

def send_email(
    to_addresses: List[str],
    subject: str,
    html_body: str,
    from_address: str = None,
    cc_addresses: List[str] = None,
    bcc_addresses: List[str] = None,
    attachments: List[Dict[str, Any]] = None,
    use_notifications_account: bool = False
) -> bool:
    """
    Send an email using O365 SMTP
    
    Args:
        to_addresses: List of recipient email addresses
        subject: Email subject line
        html_body: HTML email body content
        from_address: Override sender address (optional)
        cc_addresses: List of CC recipients (optional)
        bcc_addresses: List of BCC recipients (optional)
        attachments: List of dicts with 'filename' and 'content' keys (optional)
        use_notifications_account: Use notifications@ instead of service@ (default: False)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Determine which account to use
        if use_notifications_account:
            smtp_user = EmailConfig.NOTIFICATIONS_EMAIL
            smtp_pass = EmailConfig.NOTIFICATIONS_PASSWORD
        else:
            smtp_user = EmailConfig.SERVICE_EMAIL
            smtp_pass = EmailConfig.SERVICE_PASSWORD
        
        if not smtp_pass:
            logger.error("Email password not configured in environment variables")
            return False
        
        # Use provided from_address or default to account being used
        sender = from_address or smtp_user
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{EmailConfig.APP_NAME} <{sender}>"
        msg['To'] = ', '.join(to_addresses)
        
        if cc_addresses:
            msg['Cc'] = ', '.join(cc_addresses)
        
        # Add HTML body
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["filename"]}'
                )
                msg.attach(part)
        
        # Combine all recipients
        all_recipients = to_addresses[:]
        if cc_addresses:
            all_recipients.extend(cc_addresses)
        if bcc_addresses:
            all_recipients.extend(bcc_addresses)
        
        # Connect and send
        server = smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(sender, all_recipients, msg.as_string())
        server.quit()
        
        logger.info(f"Email sent successfully: {subject} to {to_addresses}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}", exc_info=True)
        return False


# ==============================================================================
# HELPDESK TICKET EMAIL TEMPLATES
# ==============================================================================

def email_ticket_created_user(ticket_data: Dict[str, Any]) -> bool:
    """Send confirmation email to user who created a ticket"""
    
    ticket_url = f"{EmailConfig.APP_URL}/?ticket_id={ticket_data.get('ticket_id')}"
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">Ticket Created Successfully</h2>
    
    <p>Hello {html.escape(ticket_data.get('requester_name', 'there'))},</p>
    
    <p>Your support ticket has been created and assigned ticket number <strong>#{ticket_data.get('ticket_id')}</strong>.</p>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid {EmailConfig.VDH_ORANGE}; margin: 20px 0;">
        <p style="margin: 0;"><strong>Ticket Details:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Ticket #:</strong> {ticket_data.get('ticket_id')}</li>
            <li><strong>Subject:</strong> {html.escape(ticket_data.get('subject', 'N/A'))}</li>
            <li><strong>Priority:</strong> {html.escape(ticket_data.get('priority', 'Normal'))}</li>
            <li><strong>Status:</strong> {html.escape(ticket_data.get('status', 'Open'))}</li>
            <li><strong>Location:</strong> {html.escape(ticket_data.get('location', 'N/A'))}</li>
        </ul>
    </div>
    
    <p><strong>What happens next?</strong></p>
    <ul>
        <li>Our IT team has been notified of your request</li>
        <li>You will receive updates via email as your ticket progresses</li>
        <li>Average response time: <strong>2-4 business hours</strong></li>
    </ul>
    
    {create_button('View Ticket Status', ticket_url)}
    
    <p style="margin-top: 20px;">If you have any questions or need immediate assistance, please contact us at {EmailConfig.SUPPORT_PHONE}.</p>
    
    <p>Thank you,<br><strong>VDH IT Support Team</strong></p>
    """
    
    html_email = wrap_email_template(body, f"Ticket #{ticket_data.get('ticket_id')} Created")
    
    return send_email(
        to_addresses=[ticket_data.get('requester_email')],
        subject=f"Ticket #{ticket_data.get('ticket_id')} - {ticket_data.get('subject')}",
        html_body=html_email,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]  # BCC to notifications inbox
    )


def email_ticket_created_admin(ticket_data: Dict[str, Any]) -> bool:
    """Notify admin/IT team of new ticket"""
    
    ticket_url = f"{EmailConfig.APP_URL}/?ticket_id={ticket_data.get('ticket_id')}"
    
    priority_color = {
        'Low': '#28a745',
        'Normal': '#ffc107',
        'High': '#fd7e14',
        'Critical': '#dc3545'
    }.get(ticket_data.get('priority', 'Normal'), '#ffc107')
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">🎫 New Ticket Submitted</h2>
    
    <p>A new support ticket requires attention:</p>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid {priority_color}; margin: 20px 0;">
        <p style="margin: 0;"><strong>Ticket Information:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Ticket #:</strong> {ticket_data.get('ticket_id')}</li>
            <li><strong>Subject:</strong> {html.escape(ticket_data.get('subject', 'N/A'))}</li>
            <li><strong>Priority:</strong> <span style="color: {priority_color}; font-weight: bold;">{html.escape(ticket_data.get('priority', 'Normal'))}</span></li>
            <li><strong>Category:</strong> {html.escape(ticket_data.get('category', 'N/A'))}</li>
            <li><strong>Location:</strong> {html.escape(ticket_data.get('location', 'N/A'))}</li>
            <li><strong>Requester:</strong> {html.escape(ticket_data.get('requester_name', 'N/A'))} ({ticket_data.get('requester_email', 'N/A')})</li>
            <li><strong>Phone:</strong> {html.escape(ticket_data.get('requester_phone', 'N/A'))}</li>
            <li><strong>Submitted:</strong> {ticket_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M'))}</li>
        </ul>
    </div>
    
    <p><strong>Description:</strong></p>
    <div style="background-color: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
        {html.escape(ticket_data.get('description', 'No description provided'))}
    </div>
    
    {create_button('View & Assign Ticket', ticket_url)}
    
    <p style="margin-top: 20px; font-size: 12px; color: #666;">
        This ticket has been automatically logged in the system and copied to {EmailConfig.NOTIFICATIONS_EMAIL}
    </p>
    """
    
    html_email = wrap_email_template(body, "New Ticket Notification")
    
    # Get admin emails from environment or use default
    admin_emails = os.getenv("ADMIN_EMAILS", "gclarke@vdh.virginia.gov").split(',')
    
    return send_email(
        to_addresses=admin_emails,
        subject=f"[{ticket_data.get('priority', 'Normal')}] New Ticket #{ticket_data.get('ticket_id')}: {ticket_data.get('subject')}",
        html_body=html_email,
        cc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )


def email_ticket_assigned(ticket_data: Dict[str, Any], assigned_to_name: str, assigned_to_email: str) -> bool:
    """Notify technician that a ticket has been assigned to them"""
    
    ticket_url = f"{EmailConfig.APP_URL}/?ticket_id={ticket_data.get('ticket_id')}"
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">Ticket Assigned to You</h2>
    
    <p>Hello {html.escape(assigned_to_name)},</p>
    
    <p>Ticket <strong>#{ticket_data.get('ticket_id')}</strong> has been assigned to you.</p>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid {EmailConfig.VDH_ORANGE}; margin: 20px 0;">
        <p style="margin: 0;"><strong>Ticket Details:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Subject:</strong> {html.escape(ticket_data.get('subject', 'N/A'))}</li>
            <li><strong>Priority:</strong> {html.escape(ticket_data.get('priority', 'Normal'))}</li>
            <li><strong>Requester:</strong> {html.escape(ticket_data.get('requester_name', 'N/A'))}</li>
            <li><strong>Location:</strong> {html.escape(ticket_data.get('location', 'N/A'))}</li>
        </ul>
    </div>
    
    {create_button('View Ticket', ticket_url)}
    
    <p>Please review the ticket and update its status as you work on it.</p>
    
    <p>Best regards,<br><strong>VDH Service Center</strong></p>
    """
    
    html_email = wrap_email_template(body, "Ticket Assignment")
    
    # Notify assigned technician and requester
    success = send_email(
        to_addresses=[assigned_to_email],
        subject=f"Ticket #{ticket_data.get('ticket_id')} Assigned to You",
        html_body=html_email,
        cc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )
    
    # Also notify requester that ticket was assigned
    if success:
        requester_body = f"""
        <h2 style="color: {EmailConfig.VDH_NAVY};">Ticket Update</h2>
        
        <p>Hello {html.escape(ticket_data.get('requester_name', 'there'))},</p>
        
        <p>Good news! Your ticket <strong>#{ticket_data.get('ticket_id')}</strong> has been assigned to our technician <strong>{html.escape(assigned_to_name)}</strong>.</p>
        
        <p>They will be in contact with you shortly to resolve your issue.</p>
        
        {create_button('View Ticket', ticket_url)}
        
        <p>Thank you,<br><strong>VDH IT Support Team</strong></p>
        """
        
        send_email(
            to_addresses=[ticket_data.get('requester_email')],
            subject=f"Ticket #{ticket_data.get('ticket_id')} - Assigned to Technician",
            html_body=wrap_email_template(requester_body, "Ticket Update"),
            bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
        )
    
    return success


def email_ticket_status_changed(ticket_data: Dict[str, Any], old_status: str, new_status: str, changed_by: str) -> bool:
    """Notify requester of ticket status change"""
    
    ticket_url = f"{EmailConfig.APP_URL}/?ticket_id={ticket_data.get('ticket_id')}"
    
    status_messages = {
        'In Progress': 'Your ticket is now being actively worked on.',
        'On Hold': 'Your ticket has been temporarily placed on hold. We will update you with more information soon.',
        'Resolved': 'Great news! Your ticket has been resolved.',
        'Closed': 'Your ticket has been closed. If you need further assistance, please submit a new ticket.'
    }
    
    status_color = {
        'Open': '#0066cc',
        'In Progress': '#ffc107',
        'On Hold': '#6c757d',
        'Resolved': '#28a745',
        'Closed': '#6c757d'
    }.get(new_status, '#0066cc')
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">Ticket Status Updated</h2>
    
    <p>Hello {html.escape(ticket_data.get('requester_name', 'there'))},</p>
    
    <p>The status of your ticket <strong>#{ticket_data.get('ticket_id')}</strong> has been updated.</p>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid {status_color}; margin: 20px 0;">
        <p style="margin: 0;"><strong>Status Change:</strong></p>
        <p style="margin: 10px 0;">
            <span style="text-decoration: line-through; color: #999;">{html.escape(old_status)}</span>
            →
            <span style="color: {status_color}; font-weight: bold;">{html.escape(new_status)}</span>
        </p>
        <p style="margin: 10px 0 0 0; font-size: 14px;">
            {status_messages.get(new_status, 'Your ticket status has been updated.')}
        </p>
    </div>
    
    {create_button('View Ticket Details', ticket_url)}
    
    <p style="margin-top: 20px;">Changed by: <strong>{html.escape(changed_by)}</strong></p>
    
    <p>Thank you,<br><strong>VDH IT Support Team</strong></p>
    """
    
    html_email = wrap_email_template(body, "Ticket Status Update")
    
    return send_email(
        to_addresses=[ticket_data.get('requester_email')],
        subject=f"Ticket #{ticket_data.get('ticket_id')} - Status Updated to {new_status}",
        html_body=html_email,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )


def email_ticket_resolved(ticket_data: Dict[str, Any], resolution_notes: str, resolved_by: str) -> bool:
    """Send resolution notification with satisfaction survey"""
    
    ticket_url = f"{EmailConfig.APP_URL}/?ticket_id={ticket_data.get('ticket_id')}"
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">✅ Ticket Resolved</h2>
    
    <p>Hello {html.escape(ticket_data.get('requester_name', 'there'))},</p>
    
    <p>Great news! Your ticket <strong>#{ticket_data.get('ticket_id')}</strong> has been marked as resolved.</p>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
        <p style="margin: 0;"><strong>Ticket Summary:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Subject:</strong> {html.escape(ticket_data.get('subject', 'N/A'))}</li>
            <li><strong>Resolved By:</strong> {html.escape(resolved_by)}</li>
            <li><strong>Resolution Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</li>
        </ul>
    </div>
    
    <p><strong>Resolution Notes:</strong></p>
    <div style="background-color: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
        {html.escape(resolution_notes)}
    </div>
    
    {create_button('View Ticket', ticket_url)}
    
    <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>📋 Was this resolution helpful?</strong></p>
        <p style="margin: 0; font-size: 14px;">
            If you're satisfied with the resolution, no further action is needed. The ticket will be automatically closed in 48 hours.
        </p>
        <p style="margin: 10px 0 0 0; font-size: 14px;">
            If the issue persists or you need additional help, please reply to this email or submit a new ticket.
        </p>
    </div>
    
    <p>Thank you for using VDH Crater Service Center!</p>
    
    <p>Best regards,<br><strong>VDH IT Support Team</strong></p>
    """
    
    html_email = wrap_email_template(body, "Ticket Resolved")
    
    return send_email(
        to_addresses=[ticket_data.get('requester_email')],
        subject=f"✅ Ticket #{ticket_data.get('ticket_id')} - Resolved",
        html_body=html_email,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )


def email_ticket_comment_added(ticket_data: Dict[str, Any], comment_text: str, commented_by: str) -> bool:
    """Notify requester of new comment on their ticket"""
    
    ticket_url = f"{EmailConfig.APP_URL}/?ticket_id={ticket_data.get('ticket_id')}"
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">New Comment on Your Ticket</h2>
    
    <p>Hello {html.escape(ticket_data.get('requester_name', 'there'))},</p>
    
    <p>A new comment has been added to your ticket <strong>#{ticket_data.get('ticket_id')}</strong>.</p>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid {EmailConfig.VDH_ORANGE}; margin: 20px 0;">
        <p style="margin: 0;"><strong>Comment by {html.escape(commented_by)}:</strong></p>
        <p style="margin: 10px 0; font-style: italic;">"{html.escape(comment_text)}"</p>
    </div>
    
    {create_button('View Full Conversation', ticket_url)}
    
    <p style="margin-top: 20px;">You can reply to this comment by viewing the ticket in the helpdesk portal.</p>
    
    <p>Thank you,<br><strong>VDH IT Support Team</strong></p>
    """
    
    html_email = wrap_email_template(body, "New Ticket Comment")
    
    return send_email(
        to_addresses=[ticket_data.get('requester_email')],
        subject=f"New Comment - Ticket #{ticket_data.get('ticket_id')}",
        html_body=html_email,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )


# ==============================================================================
# ASSET MANAGEMENT EMAIL TEMPLATES
# ==============================================================================

def email_asset_signed_out(asset_data: Dict[str, Any], recipient_data: Dict[str, Any], pdf_attachment: bytes = None) -> bool:
    """Send asset sign-out confirmation with PDF attachment"""
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">Asset Sign-Out Confirmation</h2>
    
    <p>Hello {html.escape(recipient_data.get('name', 'there'))},</p>
    
    <p>This confirms that the following asset has been signed out to you:</p>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid {EmailConfig.VDH_ORANGE}; margin: 20px 0;">
        <p style="margin: 0;"><strong>Asset Information:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Asset Tag:</strong> {html.escape(asset_data.get('asset_tag', 'N/A'))}</li>
            <li><strong>Description:</strong> {html.escape(asset_data.get('description', 'N/A'))}</li>
            <li><strong>Serial Number:</strong> {html.escape(asset_data.get('serial_number', 'N/A'))}</li>
            <li><strong>Sign-Out Date:</strong> {recipient_data.get('signout_date', datetime.now().strftime('%Y-%m-%d'))}</li>
        </ul>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>⚠️ Important Reminders:</strong></p>
        <ul style="margin: 0; padding-left: 20px;">
            <li>You are responsible for this asset until it is returned</li>
            <li>Report any damage or issues immediately to IT support</li>
            <li>Return the asset when no longer needed</li>
            <li>Keep the attached sign-out form for your records</li>
        </ul>
    </div>
    
    <p><strong>Contact Information:</strong></p>
    <p>If you have questions or need to return this asset, please contact:<br>
    📧 {EmailConfig.SERVICE_EMAIL}<br>
    📞 {EmailConfig.SUPPORT_PHONE}</p>
    
    <p>The signed asset form is attached to this email for your records.</p>
    
    <p>Thank you,<br><strong>VDH IT Asset Management</strong></p>
    """
    
    html_email = wrap_email_template(body, "Asset Sign-Out Confirmation")
    
    attachments = []
    if pdf_attachment:
        attachments.append({
            'filename': f'Asset_SignOut_{asset_data.get("asset_tag")}_{datetime.now().strftime("%Y%m%d")}.pdf',
            'content': pdf_attachment
        })
    
    # Send to recipient
    success = send_email(
        to_addresses=[recipient_data.get('email')],
        subject=f"Asset Sign-Out Confirmation - {asset_data.get('asset_tag')}",
        html_body=html_email,
        attachments=attachments if attachments else None,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )
    
    # Notify admin
    if success:
        admin_body = f"""
        <h2 style="color: {EmailConfig.VDH_NAVY};">Asset Signed Out</h2>
        
        <p>An asset has been signed out:</p>
        
        <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; margin: 20px 0;">
            <p style="margin: 0;"><strong>Asset:</strong> {html.escape(asset_data.get('asset_tag', 'N/A'))} - {html.escape(asset_data.get('description', 'N/A'))}</p>
            <p style="margin: 10px 0 0 0;"><strong>Signed Out To:</strong> {html.escape(recipient_data.get('name', 'N/A'))} ({recipient_data.get('email', 'N/A')})</p>
            <p style="margin: 10px 0 0 0;"><strong>Date:</strong> {recipient_data.get('signout_date', datetime.now().strftime('%Y-%m-%d'))}</p>
        </div>
        """
        
        admin_emails = os.getenv("ADMIN_EMAILS", "gclarke@vdh.virginia.gov").split(',')
        send_email(
            to_addresses=admin_emails,
            subject=f"Asset Signed Out - {asset_data.get('asset_tag')}",
            html_body=wrap_email_template(admin_body, "Asset Sign-Out Notification"),
            attachments=attachments if attachments else None,
            cc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
        )
    
    return success


def email_asset_return_reminder(asset_data: Dict[str, Any], recipient_data: Dict[str, Any], days_out: int) -> bool:
    """Send reminder to return asset"""
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">Asset Return Reminder</h2>
    
    <p>Hello {html.escape(recipient_data.get('name', 'there'))},</p>
    
    <p>This is a friendly reminder that you currently have the following asset signed out:</p>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid {EmailConfig.VDH_ORANGE}; margin: 20px 0;">
        <p style="margin: 0;"><strong>Asset Information:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Asset Tag:</strong> {html.escape(asset_data.get('asset_tag', 'N/A'))}</li>
            <li><strong>Description:</strong> {html.escape(asset_data.get('description', 'N/A'))}</li>
            <li><strong>Days Out:</strong> {days_out} days</li>
        </ul>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0;"><strong>⏰ Action Required:</strong></p>
        <p style="margin: 10px 0 0 0;">
            If you no longer need this asset, please return it to the IT department at your earliest convenience.
            If you still need the asset, please contact us to update the sign-out record.
        </p>
    </div>
    
    <p><strong>Contact:</strong> {EmailConfig.SERVICE_EMAIL} | {EmailConfig.SUPPORT_PHONE}</p>
    
    <p>Thank you,<br><strong>VDH IT Asset Management</strong></p>
    """
    
    html_email = wrap_email_template(body, "Asset Return Reminder")
    
    return send_email(
        to_addresses=[recipient_data.get('email')],
        subject=f"Reminder: Asset {asset_data.get('asset_tag')} - Please Return or Update",
        html_body=html_email,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )


# ==============================================================================
# PROCUREMENT EMAIL TEMPLATES
# ==============================================================================

def email_procurement_submitted(procurement_data: Dict[str, Any]) -> bool:
    """Confirm procurement request submission to requester"""
    
    proc_url = f"{EmailConfig.APP_URL}/?procurement_id={procurement_data.get('request_id')}"
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">Procurement Request Submitted</h2>
    
    <p>Hello {html.escape(procurement_data.get('requester_name', 'there'))},</p>
    
    <p>Your procurement request has been successfully submitted and is pending approval.</p>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid {EmailConfig.VDH_ORANGE}; margin: 20px 0;">
        <p style="margin: 0;"><strong>Request Details:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Request Number:</strong> {html.escape(procurement_data.get('request_number', 'N/A'))}</li>
            <li><strong>Description:</strong> {html.escape(procurement_data.get('item_description', 'N/A'))}</li>
            <li><strong>Total Amount:</strong> ${procurement_data.get('total_amount', 0):,.2f}</li>
            <li><strong>VITA Billing Code:</strong> {html.escape(procurement_data.get('vita_billing_code', 'N/A'))}</li>
            <li><strong>Status:</strong> Pending Approval</li>
        </ul>
    </div>
    
    <div style="background-color: #d1ecf1; border: 1px solid #0066cc; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>📋 Next Steps:</strong></p>
        <ul style="margin: 0; padding-left: 20px;">
            <li>Your request will be reviewed by the appropriate approvers</li>
            <li>You will receive email notifications as your request is processed</li>
            <li>Average approval time: 2-3 business days</li>
        </ul>
    </div>
    
    {create_button('Track Request Status', proc_url)}
    
    <p>Thank you for using the VDH procurement system!</p>
    
    <p>Best regards,<br><strong>VDH Procurement Team</strong></p>
    """
    
    html_email = wrap_email_template(body, "Procurement Request Submitted")
    
    # Send to requester
    success = send_email(
        to_addresses=[procurement_data.get('requester_email')],
        subject=f"Procurement Request {procurement_data.get('request_number')} - Submitted for Approval",
        html_body=html_email,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )
    
    # Notify approvers
    if success:
        email_procurement_needs_approval(procurement_data)
    
    return success


def email_procurement_needs_approval(procurement_data: Dict[str, Any]) -> bool:
    """Notify approvers of pending procurement request"""
    
    proc_url = f"{EmailConfig.APP_URL}/?procurement_id={procurement_data.get('request_id')}"
    
    # Determine approval tier based on amount
    total_amount = procurement_data.get('total_amount', 0)
    if total_amount < 1000:
        approval_tier = "Supervisor Approval Required"
        tier_color = "#28a745"
    elif total_amount < 5000:
        approval_tier = "Manager Approval Required"
        tier_color = "#ffc107"
    else:
        approval_tier = "Director Approval Required"
        tier_color = "#dc3545"
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">🛒 Procurement Request Awaiting Approval</h2>
    
    <p>A procurement request requires your approval:</p>
    
    <div style="background-color: {tier_color}; color: white; padding: 10px; border-radius: 5px; margin: 20px 0; text-align: center;">
        <strong>{approval_tier}</strong>
    </div>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid {EmailConfig.VDH_ORANGE}; margin: 20px 0;">
        <p style="margin: 0;"><strong>Request Information:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Request #:</strong> {html.escape(procurement_data.get('request_number', 'N/A'))}</li>
            <li><strong>Requester:</strong> {html.escape(procurement_data.get('requester_name', 'N/A'))} ({procurement_data.get('department', 'N/A')})</li>
            <li><strong>Item/Service:</strong> {html.escape(procurement_data.get('item_description', 'N/A'))}</li>
            <li><strong>Quantity:</strong> {procurement_data.get('quantity', 'N/A')}</li>
            <li><strong>Unit Price:</strong> ${procurement_data.get('unit_price', 0):,.2f}</li>
            <li><strong>Total Amount:</strong> <strong>${procurement_data.get('total_amount', 0):,.2f}</strong></li>
            <li><strong>VITA Code:</strong> {html.escape(procurement_data.get('vita_billing_code', 'N/A'))}</li>
            <li><strong>Vendor:</strong> {html.escape(procurement_data.get('vendor', 'N/A'))}</li>
        </ul>
    </div>
    
    <p><strong>Business Justification:</strong></p>
    <div style="background-color: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
        {html.escape(procurement_data.get('justification', 'No justification provided'))}
    </div>
    
    {create_button('Review & Approve Request', proc_url, EmailConfig.VDH_NAVY)}
    
    <p style="margin-top: 20px; font-size: 12px; color: #666;">
        Please review and approve/reject this request within 2 business days to ensure timely processing.
    </p>
    """
    
    html_email = wrap_email_template(body, "Procurement Approval Needed")
    
    # Get approver emails based on amount
    if total_amount < 1000:
        approver_emails = os.getenv("SUPERVISOR_EMAILS", "gclarke@vdh.virginia.gov").split(',')
    elif total_amount < 5000:
        approver_emails = os.getenv("MANAGER_EMAILS", "gclarke@vdh.virginia.gov").split(',')
    else:
        approver_emails = os.getenv("DIRECTOR_EMAILS", "gclarke@vdh.virginia.gov").split(',')
    
    return send_email(
        to_addresses=approver_emails,
        subject=f"[Action Required] Procurement Request {procurement_data.get('request_number')} - ${procurement_data.get('total_amount', 0):,.2f}",
        html_body=html_email,
        cc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )


def email_procurement_approved(procurement_data: Dict[str, Any], approved_by: str, approval_notes: str = None) -> bool:
    """Notify requester of procurement approval"""
    
    proc_url = f"{EmailConfig.APP_URL}/?procurement_id={procurement_data.get('request_id')}"
    
    body = f"""
    <h2 style="color: #28a745;">✅ Procurement Request Approved</h2>
    
    <p>Hello {html.escape(procurement_data.get('requester_name', 'there'))},</p>
    
    <p>Great news! Your procurement request <strong>{html.escape(procurement_data.get('request_number', 'N/A'))}</strong> has been approved.</p>
    
    <div style="background-color: #d4edda; border: 1px solid #28a745; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p style="margin: 0 0 10px 0;"><strong>✅ Approved By:</strong> {html.escape(approved_by)}</p>
        <p style="margin: 0;"><strong>Approval Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid #28a745; margin: 20px 0;">
        <p style="margin: 0;"><strong>Approved Request:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Item/Service:</strong> {html.escape(procurement_data.get('item_description', 'N/A'))}</li>
            <li><strong>Amount:</strong> ${procurement_data.get('total_amount', 0):,.2f}</li>
            <li><strong>Vendor:</strong> {html.escape(procurement_data.get('vendor', 'N/A'))}</li>
        </ul>
    </div>
    """
    
    if approval_notes:
        body += f"""
        <p><strong>Approval Notes:</strong></p>
        <div style="background-color: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
            {html.escape(approval_notes)}
        </div>
        """
    
    body += f"""
    <div style="background-color: #d1ecf1; border: 1px solid #0066cc; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>📋 Next Steps:</strong></p>
        <ul style="margin: 0; padding-left: 20px;">
            <li>Procurement team will process your order</li>
            <li>You will be notified when the item is ordered</li>
            <li>Contact {EmailConfig.SERVICE_EMAIL} for questions</li>
        </ul>
    </div>
    
    {create_button('View Request Details', proc_url)}
    
    <p>Thank you for using VDH Procurement!</p>
    
    <p>Best regards,<br><strong>VDH Procurement Team</strong></p>
    """
    
    html_email = wrap_email_template(body, "Procurement Request Approved")
    
    return send_email(
        to_addresses=[procurement_data.get('requester_email')],
        subject=f"✅ Procurement Request {procurement_data.get('request_number')} - Approved",
        html_body=html_email,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )


def email_procurement_rejected(procurement_data: Dict[str, Any], rejected_by: str, rejection_reason: str) -> bool:
    """Notify requester of procurement rejection"""
    
    proc_url = f"{EmailConfig.APP_URL}/?procurement_id={procurement_data.get('request_id')}"
    
    body = f"""
    <h2 style="color: #dc3545;">❌ Procurement Request Not Approved</h2>
    
    <p>Hello {html.escape(procurement_data.get('requester_name', 'there'))},</p>
    
    <p>Your procurement request <strong>{html.escape(procurement_data.get('request_number', 'N/A'))}</strong> could not be approved at this time.</p>
    
    <div style="background-color: #f8d7da; border: 1px solid #dc3545; padding: 15px; border-radius: 5px; margin: 20px 0;">
        <p style="margin: 0 0 10px 0;"><strong>Reviewed By:</strong> {html.escape(rejected_by)}</p>
        <p style="margin: 0;"><strong>Review Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    
    <p><strong>Reason for Non-Approval:</strong></p>
    <div style="background-color: white; border: 1px solid #ddd; padding: 15px; margin: 10px 0;">
        {html.escape(rejection_reason)}
    </div>
    
    <div style="background-color: #d1ecf1; border: 1px solid #0066cc; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>💡 What You Can Do:</strong></p>
        <ul style="margin: 0; padding-left: 20px;">
            <li>Review the feedback provided above</li>
            <li>Contact {html.escape(rejected_by)} for clarification if needed</li>
            <li>Submit a revised request addressing the concerns</li>
            <li>Contact procurement team for assistance: {EmailConfig.SERVICE_EMAIL}</li>
        </ul>
    </div>
    
    {create_button('View Request Details', proc_url)}
    
    <p>If you have questions about this decision, please don't hesitate to reach out.</p>
    
    <p>Best regards,<br><strong>VDH Procurement Team</strong></p>
    """
    
    html_email = wrap_email_template(body, "Procurement Request Decision")
    
    return send_email(
        to_addresses=[procurement_data.get('requester_email')],
        subject=f"Procurement Request {procurement_data.get('request_number')} - Additional Review Needed",
        html_body=html_email,
        bcc_addresses=[EmailConfig.NOTIFICATIONS_EMAIL]
    )


# ==============================================================================
# SYSTEM EMAIL TEMPLATES
# ==============================================================================

def email_password_reset(user_data: Dict[str, Any], reset_token: str) -> bool:
    """Send password reset email"""
    
    reset_url = f"{EmailConfig.APP_URL}/?reset_token={reset_token}"
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">Password Reset Request</h2>
    
    <p>Hello {html.escape(user_data.get('name', 'there'))},</p>
    
    <p>We received a request to reset your password for the VDH Crater Service Center account.</p>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>⚠️ Security Information:</strong></p>
        <ul style="margin: 0; padding-left: 20px;">
            <li>This link will expire in <strong>24 hours</strong></li>
            <li>Only use this link if you requested the password reset</li>
            <li>If you didn't request this, you can safely ignore this email</li>
        </ul>
    </div>
    
    {create_button('Reset Your Password', reset_url, '#dc3545')}
    
    <p style="margin-top: 20px;">Or copy and paste this link into your browser:</p>
    <p style="background-color: #f5f5f5; padding: 10px; word-break: break-all; font-family: monospace; font-size: 12px;">
        {reset_url}
    </p>
    
    <p>If you did not request a password reset, please contact IT support immediately at {EmailConfig.SERVICE_EMAIL}.</p>
    
    <p>Best regards,<br><strong>VDH IT Security Team</strong></p>
    """
    
    html_email = wrap_email_template(body, "Password Reset Request")
    
    return send_email(
        to_addresses=[user_data.get('email')],
        subject="VDH Service Center - Password Reset Request",
        html_body=html_email,
        use_notifications_account=True
    )


def email_new_user_welcome(user_data: Dict[str, Any], temporary_password: str) -> bool:
    """Welcome email for new user account"""
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">Welcome to VDH Crater Service Center!</h2>
    
    <p>Hello {html.escape(user_data.get('name', 'there'))},</p>
    
    <p>Your account has been created for the VDH Crater Service Center helpdesk system.</p>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; border-left: 4px solid {EmailConfig.VDH_ORANGE}; margin: 20px 0;">
        <p style="margin: 0;"><strong>Your Login Credentials:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Username:</strong> {html.escape(user_data.get('username', 'N/A'))}</li>
            <li><strong>Temporary Password:</strong> <code style="background-color: #fff; padding: 2px 6px; border-radius: 3px;">{html.escape(temporary_password)}</code></li>
            <li><strong>Login URL:</strong> <a href="{EmailConfig.APP_URL}">{EmailConfig.APP_URL}</a></li>
        </ul>
    </div>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0 0 10px 0;"><strong>⚠️ Important Security Steps:</strong></p>
        <ol style="margin: 0; padding-left: 20px;">
            <li>Login using the temporary password above</li>
            <li><strong>Change your password immediately</strong> after first login</li>
            <li>Do not share your password with anyone</li>
            <li>Use a strong, unique password</li>
        </ol>
    </div>
    
    {create_button('Login Now', EmailConfig.APP_URL)}
    
    <p><strong>What You Can Do:</strong></p>
    <ul>
        <li>Submit and track IT support tickets</li>
        <li>Request asset sign-outs</li>
        <li>Submit procurement requests</li>
        <li>Access the knowledge base</li>
        <li>View system announcements</li>
    </ul>
    
    <p>If you have any questions or need assistance, please contact us at {EmailConfig.SERVICE_EMAIL}.</p>
    
    <p>Welcome aboard!<br><strong>VDH IT Support Team</strong></p>
    """
    
    html_email = wrap_email_template(body, "Welcome to VDH Service Center")
    
    return send_email(
        to_addresses=[user_data.get('email')],
        subject="Welcome to VDH Crater Service Center - Your Account is Ready",
        html_body=html_email,
        use_notifications_account=True
    )


def email_system_maintenance(maintenance_details: Dict[str, Any]) -> bool:
    """Notify all users of scheduled maintenance"""
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">🔧 Scheduled System Maintenance</h2>
    
    <p>Dear VDH Service Center Users,</p>
    
    <p>This is to inform you of scheduled maintenance on the VDH Crater Service Center.</p>
    
    <div style="background-color: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0;"><strong>⏰ Maintenance Schedule:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Date:</strong> {html.escape(maintenance_details.get('date', 'TBD'))}</li>
            <li><strong>Start Time:</strong> {html.escape(maintenance_details.get('start_time', 'TBD'))}</li>
            <li><strong>End Time:</strong> {html.escape(maintenance_details.get('end_time', 'TBD'))}</li>
            <li><strong>Duration:</strong> Approximately {html.escape(maintenance_details.get('duration', 'TBD'))}</li>
        </ul>
    </div>
    
    <p><strong>What to Expect:</strong></p>
    <ul>
        <li>The helpdesk portal will be unavailable during this time</li>
        <li>You will not be able to submit or access tickets</li>
        <li>Email notifications may be delayed</li>
        <li>Service will be fully restored by the end time listed above</li>
    </ul>
    
    <p><strong>What You Should Do:</strong></p>
    <ul>
        <li>Save any work in progress before the maintenance window</li>
        <li>For urgent IT issues during maintenance, call {EmailConfig.SUPPORT_PHONE}</li>
        <li>Check back after the maintenance window for system updates</li>
    </ul>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; margin: 20px 0;">
        <p style="margin: 0;"><strong>Reason for Maintenance:</strong></p>
        <p style="margin: 10px 0 0 0;">{html.escape(maintenance_details.get('reason', 'System updates and improvements'))}</p>
    </div>
    
    <p>We apologize for any inconvenience and appreciate your patience as we work to improve the system.</p>
    
    <p>Best regards,<br><strong>VDH IT Systems Team</strong></p>
    """
    
    html_email = wrap_email_template(body, "Scheduled System Maintenance")
    
    # Get all user emails from environment or database
    user_emails = os.getenv("ALL_USER_EMAILS", "").split(',')
    
    if not user_emails or user_emails == ['']:
        logger.warning("No user emails configured for maintenance notification")
        return False
    
    return send_email(
        to_addresses=[EmailConfig.NOTIFICATIONS_EMAIL],  # Send to notifications as primary
        bcc_addresses=user_emails,  # BCC all users
        subject="[Important] VDH Service Center - Scheduled Maintenance Notice",
        html_body=html_email,
        use_notifications_account=True
    )


# ==============================================================================
# DAILY/WEEKLY DIGEST EMAILS
# ==============================================================================

def email_daily_ticket_summary(summary_data: Dict[str, Any]) -> bool:
    """Send daily ticket summary to administrators"""
    
    body = f"""
    <h2 style="color: {EmailConfig.VDH_NAVY};">📊 Daily Ticket Summary</h2>
    
    <p>Good morning,</p>
    
    <p>Here's your daily helpdesk activity summary for {datetime.now().strftime('%B %d, %Y')}:</p>
    
    <div style="display: flex; justify-content: space-around; margin: 20px 0;">
        <div style="background-color: #d1ecf1; padding: 15px; border-radius: 5px; text-align: center; min-width: 120px;">
            <h3 style="margin: 0; color: {EmailConfig.VDH_NAVY};">{summary_data.get('new_tickets', 0)}</h3>
            <p style="margin: 5px 0 0 0; font-size: 14px;">New Tickets</p>
        </div>
        <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; text-align: center; min-width: 120px;">
            <h3 style="margin: 0; color: {EmailConfig.VDH_NAVY};">{summary_data.get('open_tickets', 0)}</h3>
            <p style="margin: 5px 0 0 0; font-size: 14px;">Open Tickets</p>
        </div>
        <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; text-align: center; min-width: 120px;">
            <h3 style="margin: 0; color: {EmailConfig.VDH_NAVY};">{summary_data.get('resolved_tickets', 0)}</h3>
            <p style="margin: 5px 0 0 0; font-size: 14px;">Resolved</p>
        </div>
    </div>
    
    <div style="background-color: {EmailConfig.VDH_LIGHT_GRAY}; padding: 15px; margin: 20px 0;">
        <p style="margin: 0;"><strong>High Priority Items:</strong></p>
        <ul style="margin: 10px 0;">
            <li><strong>Critical Tickets:</strong> {summary_data.get('critical_tickets', 0)}</li>
            <li><strong>Overdue Tickets:</strong> {summary_data.get('overdue_tickets', 0)}</li>
            <li><strong>Pending Procurement:</strong> {summary_data.get('pending_procurement', 0)}</li>
        </ul>
    </div>
    
    {create_button('View Dashboard', EmailConfig.APP_URL)}
    
    <p>Have a great day!</p>
    
    <p>Best regards,<br><strong>VDH Service Center</strong></p>
    """
    
    html_email = wrap_email_template(body, "Daily Summary")
    
    admin_emails = os.getenv("ADMIN_EMAILS", "gclarke@vdh.virginia.gov").split(',')
    
    return send_email(
        to_addresses=admin_emails,
        subject=f"VDH Service Center - Daily Summary ({datetime.now().strftime('%m/%d/%Y')})",
        html_body=html_email,
        use_notifications_account=True
    )


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def test_email_configuration() -> bool:
    """Test email configuration by sending a test email"""
    
    body = """
    <h2 style="color: #28a745;">✅ Email System Test</h2>
    
    <p>This is a test email from the VDH Crater Service Center email automation system.</p>
    
    <p>If you're receiving this, your email configuration is working correctly!</p>
    
    <div style="background-color: #d4edda; border: 1px solid #28a745; padding: 15px; margin: 20px 0; border-radius: 5px;">
        <p style="margin: 0;"><strong>✅ Configuration Status:</strong></p>
        <ul style="margin: 10px 0;">
            <li>SMTP Server: Connected</li>
            <li>Authentication: Successful</li>
            <li>Email Templates: Loaded</li>
        </ul>
    </div>
    
    <p>Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <p>Best regards,<br><strong>VDH Service Center System</strong></p>
    """
    
    html_email = wrap_email_template(body, "Email System Test")
    
    test_email = os.getenv("TEST_EMAIL", EmailConfig.SERVICE_EMAIL)
    
    return send_email(
        to_addresses=[test_email],
        subject="VDH Service Center - Email System Test",
        html_body=html_email,
        use_notifications_account=False
    )


if __name__ == "__main__":
    # Test email configuration when run directly
    print("Testing VDH Email Automation System...")
    print(f"Service Email: {EmailConfig.SERVICE_EMAIL}")
    print(f"Notifications Email: {EmailConfig.NOTIFICATIONS_EMAIL}")
    print(f"SMTP Server: {EmailConfig.SMTP_SERVER}:{EmailConfig.SMTP_PORT}")
    
    if test_email_configuration():
        print("✅ Email test successful!")
    else:
        print("❌ Email test failed - check configuration")
