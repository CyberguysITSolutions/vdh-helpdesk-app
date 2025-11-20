# Flask Fleet Microservice

Overview
- Public vehicle procurement form: /request-trip
- Approval endpoint (from email): /approve?trip_id=<>&ts=<>&token=<>
- Return form: /return/<trip_id>
- Background job checks for unaccounted vehicles every 10 minutes.

Install & run (from repo root)
1. Create folder and files (this folder: flask_fleet)
2. Activate your existing .venv:
   cd /d C:\Users\Admin\OneDrive\Documents\GitHub\vdh-helpdesk-app
   ".venv\\Scripts\\activate.bat"

3. Install requirements:
   pip install -r flask_fleet/requirements.txt

4. Set required environment variables OR add them to .streamlit/secrets.toml under a top-level section:
   SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FLEET_MANAGER_EMAIL, HMAC_SECRET, APP_BASE_URL

   Example Windows (cmd):
     setx SMTP_HOST "smtp.example.com"
     setx SMTP_PORT "587"
     setx SMTP_USER "noreply@example.com"
     setx SMTP_PASS "supersecret"
     setx FLEET_MANAGER_EMAIL "fleet.manager@example.com"
     setx HMAC_SECRET "very-secret-value"
     setx APP_BASE_URL "https://your-public-host"

   Or add to .streamlit/secrets.toml (local only):
   [email]
   host = "smtp.example.com"
   port = 587
   user = "noreply@example.com"
   pass = "supersecret"

   [security]
   hmac_secret = "very-secret-value"

5. Run the service:
   ".venv\\Scripts\\python.exe" flask_fleet/app.py

Expose it publicly
- For one-off testing, you can use ngrok to expose the localhost port and set APP_BASE_URL accordingly.
- For production, host in Azure App Service, container, or VM and set APP_BASE_URL to the public domain.

Notes
- The Flask app uses fleet.fleet_db.get_conn() to reuse your existing DB connection helper.
- The approval link is HMAC signed and time-limited (default 7 days). You can change token parameters in token_utils.py.
- The 4-hour unaccounted check runs via APScheduler in the service. For production reliability, consider running this as an Azure Function or scheduled job instead.