# Fleet Management Feature — Plan (Updated with Work Location & Reports)

Overview
- Add fleet management to Streamlit app using Azure SQL.
- Users can sign out/return vehicles; admin can add vehicles, reset service, and run advanced reports.
- New field: work_location (the VDH location from which the vehicle is dispatched).

Database
- New tables: vehicles, trip_logs (includes work_location), service_logs, fleet_alerts.
- Indexes added for location and date queries to support advanced reports.

Key behaviours
- Sign-out form captures: driver, driver contact, work_location, destination, purpose, departure_time, mileage_departure.
- Return form captures: return_time, mileage_return and computes miles_used.
- miles_until_service is recalculated when trip completed or when service log resets counter.
- Vehicles overdue (miles_until_service <= 0) are displayed as unavailable in the UI.
- Vehicles are ordered from least-used to most-used by miles_per_month for selection.

Reports
- Advanced reports UI enables filtering by date range, location, vehicle, driver, status.
- Reports can be exported as CSV.

Configuration (st.secrets)
- database: as already present in repo for Azure SQL
- blob: optional, for Azure Blob Storage uploads: account_name, key, container
- fleet:
  - service_threshold: integer (e.g., 0 or 500)
  - monthly_target_miles: integer (e.g., 500)

Next steps to deploy
1. Apply the SQL migration to your staging DB.
2. Add the Python files to the repo under fleet/ and import fleet.fleet_ui into helpdesk_app.py.
3. Add Blob storage credentials to st.secrets if using receipts/photos.
4. Optionally schedule alerts_job.py as a daily Azure Function or cron job to email/post alerts.

Security & Permissions
- Restrict admin-only actions (add vehicle, reset service, view all reports) based on your users table / roles.
- Do not commit secrets to the repo; use Streamlit secrets or Azure Key Vault.
