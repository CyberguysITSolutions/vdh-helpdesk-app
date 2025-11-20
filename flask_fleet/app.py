#!/usr/bin/env python3
"""
Flask microservice for external vehicle procurement/return and approval links.

Run:
  Activate your .venv, then:
  ".venv\\Scripts\\python.exe" app.py

Or using flask CLI:
  set FLASK_APP=app.py
  ".venv\\Scripts\\flask.exe" run --host=0.0.0.0 --port=5001
"""
from flask import Flask, request, render_template_string, redirect, url_for, flash
from datetime import datetime, timezone, timedelta
import base64
import traceback
import os
import io

from fleet import fleet_db
from token_utils import make_token, verify_token
from email_utils import send_email

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "change-me-for-prod")  # for flashing messages in templates

# Load config from environment or .streamlit/secrets.toml via helper inside token_utils/email_utils
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5001")  # used to build approval URLs
FLEET_MANAGER_EMAIL = os.getenv("FLEET_MANAGER_EMAIL") or None

# HTML templates (minimal). You can replace with real templates later.
REQUEST_FORM_HTML = """
<!doctype html>
<title>Request a Vehicle</title>
<h2>Vehicle Request Form</h2>
<form method="post" enctype="multipart/form-data">
  <label for="vehicle_id">Vehicle:</label><br>
  <select name="vehicle_id" required>
    {% for v in vehicles %}
      <option value="{{v['id']}}">[{{v['status']}}] {{v['make_model']}} (plate: {{v['license_plate']}}) - current_mileage: {{v['current_mileage']}}</option>
    {% endfor %}
  </select><br><br>

  <label>First name*</label><br><input name="first" required><br>
  <label>Last name*</label><br><input name="last" required><br>
  <label>Email*</label><br><input name="email" type="email" required><br>
  <label>Phone</label><br><input name="phone"><br>
  <label>Destination</label><br><input name="destination"><br>
  <label>Departure (local datetime)</label><br><input name="departure_time" type="datetime-local" value="{{now}}"><br><br>

  <button type="submit">Request Vehicle</button>
</form>
"""

APPROVAL_RESULT_HTML = """
<!doctype html>
<title>Approval Result</title>
<h2>Approval Result</h2>
<p>{{message}}</p>
"""

RETURN_FORM_HTML = """
<!doctype html>
<title>Return Vehicle</title>
<h2>Return Vehicle - Trip {{trip_id}}</h2>
<form method="post" enctype="multipart/form-data">
  <label>Returning Mileage*</label><br><input name="returning_mileage" type="number" required><br>
  <label>Return time</label><br><input name="return_time" type="datetime-local" value="{{now}}"><br>
  <label>Notes</label><br><textarea name="notes"></textarea><br>
  <label>Upload receipts (multiple allowed)</label><br><input name="receipts" type="file" multiple><br><br>
  <button type="submit">Submit Return</button>
</form>
"""

def ordered_vehicles():
    """
    Query vehicles ordering:
      - Available first, then other statuses
      - Within same availability order by usage_count (least used first)
    """
    conn = fleet_db.get_conn()
    cur = conn.cursor()
    q = """
        SELECT id, year, make_model, vin, license_plate, photo_url, initial_mileage, current_mileage, status, usage_count
        FROM dbo.vehicles
        ORDER BY
          CASE WHEN status = 'Available' THEN 0
               WHEN status = 'In Use' THEN 1
               WHEN status = 'Maintenance' THEN 2
               WHEN status = 'Out of Service' THEN 3
               ELSE 4 END,
          ISNULL(usage_count, 0) ASC,
          id ASC
    """
    cur.execute(q)
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows

@app.route("/request-trip", methods=["GET", "POST"])
def request_trip():
    if request.method == "GET":
        vehicles = ordered_vehicles()
        now = datetime.now().strftime("%Y-%m-%dT%H:%M")
        return render_template_string(REQUEST_FORM_HTML, vehicles=vehicles, now=now)

    # POST: create trip request and notify fleet manager
    try:
        form = request.form
        vehicle_id = int(form["vehicle_id"])
        first = form.get("first", "").strip()
        last = form.get("last", "").strip()
        email = form.get("email", "").strip()
        phone = form.get("phone", "").strip()
        destination = form.get("destination", "").strip()
        departure_time = form.get("departure_time")
        departure_dt = None
        if departure_time:
            # parse local datetime from form, treat as naive local time and convert to UTC offsetless string
            departure_dt = datetime.fromisoformat(departure_time)

        # get starting mileage from vehicles.current_mileage
        conn = fleet_db.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT current_mileage FROM dbo.vehicles WHERE id = ?", vehicle_id)
        r = cur.fetchone()
        starting_mileage = int(r[0]) if r and r[0] is not None else None

        # Insert Vehicle_Trips (status = Requested)
        insert_sql = """
            INSERT INTO dbo.Vehicle_Trips (vehicle_id, requester_first, requester_last, requester_email, requester_phone, starting_mileage, destination, departure_time, status)
            OUTPUT INSERTED.trip_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Requested')
        """
        # pyodbc with OUTPUT INSERTED.trip_id returns row with trip_id
        cur.execute(insert_sql, (vehicle_id, first, last, email, phone, starting_mileage, destination, departure_dt))
        trip_id_row = cur.fetchone()
        if trip_id_row:
            trip_id = int(trip_id_row[0])
        else:
            # fallback: try SCOPE_IDENTITY
            cur.execute("SELECT CAST(SCOPE_IDENTITY() AS INT)")
            trip_id = int(cur.fetchone()[0])
        conn.commit()
        cur.close()
        conn.close()

        # Create approval token and email to fleet manager
        token, ts = make_token(trip_id)
        approve_url = f"{APP_BASE_URL}/approve?trip_id={trip_id}&ts={ts}&token={token}"

        subject = f"[Fleet] Approval request for vehicle trip #{trip_id}"
        body = f"""
A new vehicle request has been submitted.

Trip ID: {trip_id}
Requester: {first} {last} ({email})
Vehicle ID: {vehicle_id}
Destination: {destination}
Departure: {departure_dt}

Approve this trip:
{approve_url}

(If you did not expect this email, ignore it.)
"""
        send_email(to_addr=FLEET_MANAGER_EMAIL, subject=subject, body=body)

        return render_template_string(APPROVAL_RESULT_HTML, message="Request submitted. Fleet manager has been notified for approval.")
    except Exception as exc:
        traceback.print_exc()
        return render_template_string(APPROVAL_RESULT_HTML, message=f"Failed to submit request: {exc}")

@app.route("/approve")
def approve():
    """Approval link clicked by fleet manager. Validates token and approves trip by calling stored proc."""
    trip_id = request.args.get("trip_id")
    token = request.args.get("token")
    ts = request.args.get("ts")
    approver = request.args.get("approver") or "Fleet Manager (email link)"

    if not trip_id or not token or not ts:
        return render_template_string(APPROVAL_RESULT_HTML, message="Missing parameters")

    ok, msg = verify_token(int(trip_id), token, ts)
    if not ok:
        return render_template_string(APPROVAL_RESULT_HTML, message=f"Invalid or expired token: {msg}")

    try:
        conn = fleet_db.get_conn()
        cur = conn.cursor()

        # Check current trip status
        cur.execute("SELECT vehicle_id, status, requester_first, requester_last FROM dbo.Vehicle_Trips WHERE trip_id = ?", int(trip_id))
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return render_template_string(APPROVAL_RESULT_HTML, message="Trip not found")

        vehicle_id, status, rq_first, rq_last = row[0], row[1], row[2], row[3]
        if status not in ("Requested",):
            cur.close()
            conn.close()
            return render_template_string(APPROVAL_RESULT_HTML, message=f"Trip is not in a state that can be approved (current status: {status})")

        # Call stored proc to approve and set vehicle current_trip_id / usage_count
        cur.execute("EXEC dbo.sp_ApproveVehicleTrip ?, ?", int(trip_id), approver)

        # Update vehicle current_driver to requester name
        cur.execute("UPDATE dbo.vehicles SET current_driver = ? WHERE id = ?", f"{rq_first} {rq_last}", vehicle_id)

        conn.commit()
        cur.close()
        conn.close()

        # Notify requester by email
        subject = f"[Fleet] Your vehicle request #{trip_id} has been approved"
        body = f"Your request #{trip_id} for vehicle {vehicle_id} has been approved by {approver}."
        send_email(to_addr=request.args.get("requester_email") or "", subject=subject, body=body)

        return render_template_string(APPROVAL_RESULT_HTML, message=f"Trip {trip_id} approved successfully.")
    except Exception as e:
        traceback.print_exc()
        return render_template_string(APPROVAL_RESULT_HTML, message=f"Approval failed: {e}")

@app.route("/return/<int:trip_id>", methods=["GET", "POST"])
def return_trip(trip_id):
    if request.method == "GET":
        now = datetime.now().strftime("%Y-%m-%dT%H:%M")
        return render_template_string(RETURN_FORM_HTML, trip_id=trip_id, now=now)

    # POST: process return
    try:
        form = request.form
        returning_mileage = form.get("returning_mileage")
        return_time = form.get("return_time")
        notes = form.get("notes", "")

        returning_mileage_val = int(returning_mileage) if returning_mileage else None
        return_time_val = datetime.fromisoformat(return_time) if return_time else None

        conn = fleet_db.get_conn()
        cur = conn.cursor()

        # Call stored proc to mark as returned
        cur.execute("EXEC dbo.sp_ReturnVehicleTrip ?, ?, ?, ?", trip_id, returning_mileage_val, return_time_val, notes)

        # Save any uploaded receipts
        files = request.files.getlist("receipts")
        for f in files:
            if f and f.filename:
                data = f.read()
                cur.execute(
                    "INSERT INTO dbo.Vehicle_Trip_Receipts (trip_id, filename, content_type, file_data) VALUES (?, ?, ?, ?)",
                    trip_id, f.filename, f.content_type, pyodbc.Binary(data) if 'pyodbc' in globals() else data
                )

        conn.commit()
        cur.close()
        conn.close()

        return render_template_string(APPROVAL_RESULT_HTML, message=f"Trip {trip_id} marked as returned. Thank you.")
    except Exception as e:
        traceback.print_exc()
        return render_template_string(APPROVAL_RESULT_HTML, message=f"Return processing failed: {e}")

# Background job: unaccounted notification
def check_unaccounted():
    """
    Find trips that are In Use with departure_time older than 4 hours and notification_unaccounted_sent = 0.
    Send email to admin and driver, and set notification_unaccounted_sent = 1.
    """
    try:
        conn = fleet_db.get_conn()
        cur = conn.cursor()
        threshold = datetime.now(timezone.utc) - timedelta(hours=4)
        q = """
            SELECT trip_id, vehicle_id, requester_first, requester_last, requester_email, departure_time
            FROM dbo.Vehicle_Trips
            WHERE status = 'In Use' AND notification_unaccounted_sent = 0 AND departure_time <= ?
        """
        cur.execute(q, threshold)
        rows = cur.fetchall()
        for r in rows:
            trip_id, vehicle_id, first, last, email_addr, depart = r
            subject = f"[Fleet] Vehicle {vehicle_id} unaccounted for - Trip {trip_id}"
            body = f"Trip {trip_id} for vehicle {vehicle_id} departed at {depart} and is unaccounted for. Please return vehicle and close the trip log."
            # send to both admin and driver
            send_email(to_addr=FLEET_MANAGER_EMAIL, subject=subject, body=body)
            if email_addr:
                send_email(to_addr=email_addr, subject=subject, body=body)
            # set flag
            cur.execute("UPDATE dbo.Vehicle_Trips SET notification_unaccounted_sent = 1 WHERE trip_id = ?", trip_id)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("check_unaccounted error:", e)
        traceback.print_exc()

# Optionally start scheduler when run directly
def start_scheduler(app):
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        sched = BackgroundScheduler()
        sched.add_job(check_unaccounted, "interval", minutes=10, id="unaccounted_check", replace_existing=True)
        sched.start()
    except Exception as e:
        print("Scheduler not started:", e)

if __name__ == "__main__":
    # start scheduler for background notifications
    start_scheduler(app)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=False)