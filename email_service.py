import requests
import os


def get_token():
    """Get an OAuth2 access token from Microsoft identity platform."""
    url = f"https://login.microsoftonline.com/{os.environ['AZURE_TENANT_ID']}/oauth2/v2.0/token"
    res = requests.post(url, data={
        "grant_type": "client_credentials",
        "client_id": os.environ["AZURE_CLIENT_ID"],
        "client_secret": os.environ["AZURE_CLIENT_SECRET"],
        "scope": "https://graph.microsoft.com/.default"
    })
    res.raise_for_status()
    return res.json()["access_token"]


def send_email(to, subject, body):
    """
    Send an email via Microsoft Graph API.

    Args:
        to      (str): Recipient email address
        subject (str): Email subject line
        body    (str): HTML email body content

    Returns:
        int: HTTP status code (202 = success)

    Required environment variables:
        AZURE_TENANT_ID     - Your Azure AD tenant ID
        AZURE_CLIENT_ID     - Your App Registration client ID
        AZURE_CLIENT_SECRET - Your App Registration client secret
        EMAIL_FROM          - Sender address e.g. notifications@craterservicecenter.com
    """
    token = get_token()
    from_email = os.environ["EMAIL_FROM"]

    response = requests.post(
        f"https://graph.microsoft.com/v1.0/users/{from_email}/sendMail",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body
                },
                "toRecipients": [
                    {"emailAddress": {"address": to}}
                ]
            }
        }
    )

    return response.status_code  # 202 = accepted/success


# ── Example usage ────────────────────────────────────────────────────────────
# Import and call send_email() from anywhere in your app:
#
#   from email_service import send_email
#
#   def submit_service_request(customer_email, request_details):
#       send_email(
#           to=customer_email,
#           subject="Your Service Request - VDH Crater Service Center",
#           body=f"""
#               <h2>Service Request Received</h2>
#               <p>Thank you for contacting VDH Crater Service Center.</p>
#               <p>Request details: {request_details}</p>
#               <p>We will be in touch shortly.</p>
#           """
#       )
