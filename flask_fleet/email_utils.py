"""
email_utils.py

Simple SMTP sender using configuration from environment variables or .streamlit/secrets.toml:

Required:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FLEET_MANAGER_EMAIL

Optional:
  FROM_ADDRESS (defaults to SMTP_USER)
"""
import os
import smtplib
from email.message import EmailMessage
import traceback

def _load_conf():
    cfg = {}
    cfg['host'] = os.getenv("SMTP_HOST")
    cfg['port'] = int(os.getenv("SMTP_PORT") or 587)
    cfg['user'] = os.getenv("SMTP_USER")
    cfg['password'] = os.getenv("SMTP_PASS")
    cfg['from_addr'] = os.getenv("FROM_ADDRESS") or cfg['user']
    cfg['fleet_manager'] = os.getenv("FLEET_MANAGER_EMAIL")
    return cfg

def send_email(to_addr: str, subject: str, body: str):
    cfg = _load_conf()
    if not cfg['host'] or not cfg['user'] or not cfg['password']:
        print("SMTP config missing; cannot send email.")
        return False

    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = cfg['from_addr']
        msg["To"] = to_addr
        msg.set_content(body)

        with smtplib.SMTP(cfg['host'], cfg['port']) as s:
            s.starttls()
            s.login(cfg['user'], cfg['password'])
            s.send_message(msg)
        return True
    except Exception as e:
        print("send_email error:", e)
        traceback.print_exc()
        return False