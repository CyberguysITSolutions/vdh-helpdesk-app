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
