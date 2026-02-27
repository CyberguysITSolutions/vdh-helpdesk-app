---
Summary
- Adds a Fleet Management feature to the VDH HelpDesk Streamlit app.
- Provides DB schema (vehicles, trip_logs, service_logs, fleet_alerts), Streamlit modules for fleet UI and helpers, service reset flow, and an advanced reporting UI.
- Files added on feature/fleet-management:
  - db/migrations/20251030_create_fleet_tables.sql (DB migration)
  - fleet/fleet_db.py (DB helpers)
  - fleet/fleet_ui.py (Streamlit UI pages: vehicle list, sign-out, return, admin dashboard, reports)
  - fleet/service_reset.py (service reset UI and blob upload helper)
  - fleet/reports_ui.py (reporting UI)
  - docs/FLEET_FEATURE_PLAN.md (feature plan & deployment notes)

Important notes / warnings
- Do NOT commit secrets to the repository. Use Streamlit secrets or Azure Key Vault.
- Apply the SQL migration to a STAGING database first (Azure Data Studio or sqlcmd) — do not run on production before testing.
- Configure st.secrets for:
  - database (already present in repo)
  - blob (optional) — keys: account_name, key, container
  - fleet (optional) — keys: service_threshold (int), monthly_target_miles (int)
- I did NOT modify helpdesk_app.py in this PR. Integration into the main app (importing and mounting the fleet UI) must be done in a follow-up change — back up helpdesk_app.py before editing or merging that follow-up.

Testing checklist (run these on staging)
1. Run the migration on staging DB and confirm tables created:
   - dbo.vehicles, dbo.trip_logs, dbo.service_logs, dbo.fleet_alerts
2. Sign-out flow:
   - Select a vehicle, sign out (driver, work_location, mileage_departure) → verify a row in dbo.trip_logs with status = 'active' and vehicle.status = 'dispatched'
3. Return flow:
   - Complete return with mileage_return → verify miles_used computed, trip status = 'completed', vehicle.current_mileage updated, and vehicle.miles_until_service adjusted (4000 - (current - last_service_mileage))
4. Service reset:
   - Use reset UI to create service log → verify a new row in dbo.service_logs and vehicle.last_service_mileage updated to current_mileage and miles_until_service reset to 4000
5. Reporting:
   - Generate a report by date / work_location and export CSV → confirm data and columns (trip_id, vehicle_id, make_model, license_plate, driver_name, driver_contact, work_location, destination, purpose, departure_time, return_time, mileage_departure, mileage_return, miles_used, status)
6. Overdue behavior:
   - Vehicles with miles_until_service <= 0 should show as unavailable (greyed / disabled in the UI)

PR checklist and reviewers / labels
- Request review from: CyberguysITSolutions
- Labels to add: feature, fleet-management
- Status: Ready for review (not a draft)

Merge notes
- Merge only after migration verified on staging and the follow-up integration of fleet UI into helpdesk_app.py is tested (or do the integration in a separate PR and test there).
- If you want me to create the follow-up that integrates the Fleet UI into helpdesk_app.py, I can prepare that change after you confirm a backup was taken.
---