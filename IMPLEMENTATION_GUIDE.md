# Public Forms Refactor - Implementation Guide

## Overview
This PR implements Option 3: refactoring public form scripts so the same Streamlit app can serve public-facing forms at friendly routes and submit to the same DB used by the admin UI.

## Changes Summary

### New Files Created
1. **`public_forms.py`** - New module containing three public form render functions
2. **`db/migrations/001_add_workflow_columns.sql`** - Optional migration for workflow columns

### Modified Files
1. **`helpdesk_app.py`** - Added router, sidebar deep-links, admin workflow features

## Detailed Changes

### 1. Public Forms Module (`public_forms.py`)
Created a new module with three render functions:
- `render_public_ticket_form(insert_callback=None)` - Renders ticket submission form
- `render_public_vehicle_request_form(insert_callback=None)` - Renders vehicle request form  
- `render_public_procurement_form(insert_callback=None)` - Renders procurement request form

**Features:**
- Each function validates required fields
- Inserts into appropriate DB table with proper status
- Shows success confirmation with record ID
- Supports custom `insert_callback` for testing
- Includes `insert_and_get_id()` helper to return new record IDs
- Full MOCK_DATA mode support for testing without DB

**Status Values:**
- Tickets: `status='New'` (changed from 'draft')
- Vehicle Requests: `status='Requested'` (changed from 'draft')
- Procurement: `status='Requested'` (changed from 'draft')

### 2. Router in `helpdesk_app.py`
Added router logic at the top of the file (after `st.set_page_config()`):
- Reads query parameters using `st.query_params` or `st.experimental_get_query_params()`
- Routes to public forms based on `page` parameter
- Supported routes:
  - `?page=helpdesk_ticket/submit` → Ticket form
  - `?page=fleetmanagement/requestavehicle` → Vehicle request form
  - `?page=procurement/submitrequisition` → Procurement form
- Calls `st.stop()` after rendering public form to prevent admin UI rendering
- Also accepts paths with dashes: `helpdesk_ticket-submit`, etc.

### 3. Sidebar Deep-Link Buttons
Added HTML buttons in sidebar for easy access to public forms:
- Styled with VDH orange color (#FF6B35)
- Open in new tab when clicked
- Use relative URLs with query parameters
- Available to both admin and public users

### 4. Admin Workflow Features

#### Tickets Page (`🎫 Tickets`)
- Shows "🔴 NEW" badge for tickets with `status='New'` AND `first_response_at IS NULL`
- View Details button marks ticket as viewed by setting `first_response_at = GETDATE()`
- Removes NEW badge after first view
- Query includes `is_new` calculated field for highlighting

#### Procurement Page (`🛒 Procurement`)
- Shows "🆕 NEW REQUEST" badge for requests with `status='Requested'`
- Displays full request details including justification
- Approve button: Sets `status='Approved'`, `approved_at=GETDATE()`
- Deny button: Sets `status='Denied'`
- Page refreshes after approve/deny action

#### Fleet Page (`🚗 Fleet`)
- Added "Vehicle Requests" tab showing pending requests
- Lists all requests with `status='Requested'`
- Each request shows in expanded expander with full details
- Approve button: Sets `status='Approved'`, `approved_at=GETDATE()`
- Deny button: Sets `status='Denied'`, captures optional `denial_reason`
- Page refreshes after approve/deny action

### 5. Helper Functions

#### `insert_and_get_id(query, params=None)`
- Executes INSERT query
- Returns `(new_id, None)` on success or `(None, error_message)` on failure
- Uses `SELECT @@IDENTITY AS id` to get last inserted ID
- Supports MOCK_DATA mode (returns fake ID based on hash)

#### MOCK_DATA Support
- Both `insert_and_get_id()` and `execute_non_query()` in `public_forms.py` check `MOCK_DATA` env var
- When `MOCK_DATA=1`, no DB connection is made
- Returns mock data for testing

### 6. Database Migration (Optional)

File: `db/migrations/001_add_workflow_columns.sql`

Adds columns if they don't exist:
- `dbo.Tickets.first_response_at` (DATETIME NULL) - Tracks when admin first views ticket
- `dbo.Procurement_Requests.approved_by` (NVARCHAR(100) NULL) - Who approved
- `dbo.Procurement_Requests.approved_at` (DATETIME NULL) - When approved
- `dbo.Vehicle_Trips.approved_by` (NVARCHAR(100) NULL) - Who approved
- `dbo.Vehicle_Trips.approved_at` (DATETIME NULL) - When approved
- `dbo.Vehicle_Trips.denial_reason` (NVARCHAR(500) NULL) - Reason if denied

**Note:** This migration is OPTIONAL. The app will work without these columns, but:
- NEW badges for tickets won't work without `first_response_at`
- Approval tracking won't be recorded without `approved_by`/`approved_at`

## Testing Instructions

### Local Testing with MOCK_DATA (No Database Required)

1. **Set MOCK_DATA environment variable:**
   ```bash
   export MOCK_DATA=1
   ```

2. **Run the Streamlit app:**
   ```bash
   streamlit run helpdesk_app.py
   ```

3. **Test public form routes:**
   - Open browser to `http://localhost:8501`
   - Click on sidebar deep-link buttons to open forms in new tabs
   - Or manually navigate to:
     - `http://localhost:8501?page=helpdesk_ticket/submit`
     - `http://localhost:8501?page=fleetmanagement/requestavehicle`
     - `http://localhost:8501?page=procurement/submitrequisition`
   - Submit each form - should show success with mock ID

4. **Test admin features:**
   - Sign in as admin (requires `ADMIN_PASSWORD` env var or secrets)
   - Navigate to:
     - 🎫 Tickets - Check if NEW badges appear (may need mock data)
     - 🛒 Procurement - Check if NEW REQUEST badges appear
     - 🚗 Fleet → Vehicle Requests tab - Check approve/deny buttons

### Testing with Real Database

1. **Configure database secrets:**
   Create `.streamlit/secrets.toml` or `..streamlit/secrets.toml`:
   ```toml
   [database]
   server = "your-server.database.windows.net"
   database = "helpdesk-db"
   username = "your_username"
   password = "your_password"

   [admin]
   password = "your_admin_password"
   ```

2. **Run optional migration (if needed):**
   ```sql
   -- Connect to your database and run:
   -- db/migrations/001_add_workflow_columns.sql
   ```

3. **Run the app:**
   ```bash
   streamlit run helpdesk_app.py
   ```

4. **Test public submission flow:**
   - Navigate to each public form route
   - Submit test data
   - Verify records are inserted into DB with correct status:
     - `dbo.Tickets` with `status='New'`
     - `dbo.Vehicle_Trips` with `status='Requested'`
     - `dbo.Procurement_Requests` with `status='Requested'`

5. **Test admin workflow:**
   - Sign in as admin
   - Go to Tickets page:
     - NEW badge should appear on new tickets
     - Click "View Details" - badge should disappear after refresh
     - Verify `first_response_at` is set in DB
   - Go to Procurement page:
     - NEW REQUEST badge should appear
     - Click Approve/Deny - status should update in DB
   - Go to Fleet → Vehicle Requests:
     - Pending requests should show
     - Click Approve - status should change to 'Approved'
     - Click Deny - can add reason, status changes to 'Denied'

### Testing Deep-Link Sharing

1. **Copy deep-link URL from sidebar button**
2. **Open in incognito/private browser window** (to test as non-admin user)
3. **Verify form renders correctly**
4. **Submit form and verify success message**

### Verification Checklist

- [ ] Public ticket form accessible via query param route
- [ ] Public vehicle request form accessible via query param route
- [ ] Public procurement form accessible via query param route
- [ ] Sidebar deep-link buttons open forms in new tab
- [ ] Forms submit successfully and return record ID
- [ ] Admin Tickets page shows NEW badges
- [ ] Viewing ticket removes NEW badge and sets first_response_at
- [ ] Admin Procurement page shows NEW REQUEST badges
- [ ] Approve/Deny buttons work for procurement
- [ ] Admin Fleet page shows pending vehicle requests
- [ ] Approve/Deny buttons work for fleet requests
- [ ] All features work in MOCK_DATA mode
- [ ] No errors in browser console
- [ ] No Python exceptions in Streamlit logs

## Troubleshooting

### "fleet_db import error"
- Ensure `fleet/fleet_db.py` exists
- Check that `fleet/__init__.py` is present

### Query params not working
- Try both `?page=helpdesk_ticket/submit` and `?page=helpdesk_ticket-submit`
- Check browser URL bar shows the query parameter
- Refresh the page

### NEW badges not showing
- Run the optional migration to add `first_response_at` column
- Verify tickets have `status='New'` in database
- Check that `first_response_at IS NULL`

### Forms not submitting in MOCK_DATA mode
- Verify `MOCK_DATA=1` is set
- Check console for any Python errors
- Try restarting the Streamlit server

### Deep-link buttons not styled
- Check that HTML/CSS is rendered (view page source)
- Try different browser
- Check Streamlit version supports `unsafe_allow_html=True`

## Security Notes

- All queries use parameterized statements to prevent SQL injection
- No secrets or credentials are hardcoded
- Admin password required for admin features
- Public forms are accessible without authentication (by design)
- Deep-link URLs can be shared publicly

## Future Enhancements

Potential improvements for future PRs:
- Email notifications when requests are approved/denied
- Attach files to forms
- More detailed vehicle assignment in Fleet approval
- Audit log for approval actions
- Bulk approve/deny operations
- Export pending requests to Excel/PDF
- Public form confirmation emails
- Rate limiting for public forms
- CAPTCHA on public forms

## Related Issues

This PR addresses the requirement to:
- Refactor public form scripts
- Enable in-app routing for public forms
- Wire DB inserts with admin approval flows
- Add admin highlights for new submissions
- Support MOCK_DATA mode for testing

---

**Testing Status:** ✅ Syntax validated, ready for review
**Migration Required:** Optional - see migration file
**Breaking Changes:** None - backwards compatible
