import pyodbc
import streamlit as st
import pandas as pd
from datetime import datetime

def get_conn():
    db = st.secrets["database"]
    conn_str = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={{db['server']}};DATABASE={{db['database']}};"
        f"UID={{db['username']}};PWD={{db['password']}};Encrypt=yes;TrustServerCertificate=no;"
    )
    return pyodbc.connect(conn_str, autocommit=False)

def fetch_vehicles(order_by_usage=True):
    conn = get_conn()
    cur = conn.cursor()
    q = """
    SELECT v.id, v.year, v.make_model, v.license_plate, v.photo_url, v.current_mileage,
      v.initial_mileage, v.last_service_mileage, v.last_service_date, v.miles_until_service,
      v.status, v.created_at,
      CASE WHEN DATEDIFF(month, v.created_at, SYSUTCDATETIME()) = 0 THEN
           (v.current_mileage - v.initial_mileage) * 1.0
      ELSE (v.current_mileage - v.initial_mileage) * 1.0 / NULLIF(DATEDIFF(month, v.created_at, SYSUTCDATETIME()),0)
      END AS miles_per_month
    FROM dbo.vehicles v
    """
    if order_by_usage:
        q += " ORDER BY miles_per_month ASC"
    cur.execute(q)
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return rows

def create_vehicle(payload):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
      INSERT INTO dbo.vehicles (year, make_model, vin, license_plate, photo_url, initial_mileage, current_mileage, last_service_mileage, last_service_date, miles_until_service, status, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME(), SYSUTCDATETIME())
    """, (
        payload.get('year'),
        payload['make_model'],
        payload.get('vin'),
        payload.get('license_plate'),
        payload.get('photo_url'),
        payload.get('initial_mileage', 0),
        payload.get('initial_mileage', 0),
        payload.get('last_service_mileage'),
        payload.get('last_service_date'),
        payload.get('miles_until_service', 4000),
        payload.get('status', 'motorpool')
    ))
    conn.commit()
    conn.close()

def create_trip(payload):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
      INSERT INTO dbo.trip_logs
      (vehicle_id, driver_user_id, driver_name, driver_phone, driver_email, work_location, destination, purpose, departure_time, mileage_departure, status, created_at, updated_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', SYSUTCDATETIME(), SYSUTCDATETIME())
    """, (
        payload['vehicle_id'],
        payload.get('driver_user_id'),
        payload.get('driver_name'),
        payload.get('driver_phone'),
        payload.get('driver_email'),
        payload.get('work_location'),
        payload.get('destination'),
        payload.get('purpose'),
        payload['departure_time'],
        payload['mileage_departure'],
    ))
    cur.execute("UPDATE dbo.vehicles SET status='dispatched', updated_at=SYSUTCDATETIME() WHERE id = ?", (payload['vehicle_id'],))
    conn.commit()
    conn.close()

def complete_trip(trip_id, mileage_return, return_time=None):
    conn = get_conn()
    cur = conn.cursor()
    return_time = return_time or datetime.utcnow()
    cur.execute("SELECT vehicle_id, mileage_departure FROM dbo.trip_logs WHERE id = ?", (trip_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError("Trip not found")
    vehicle_id, mileage_departure = row
    miles_used = mileage_return - mileage_departure
    if miles_used < 0:
        conn.close()
        raise ValueError("Return mileage less than departure mileage")
    cur.execute("""
      UPDATE dbo.trip_logs
      SET mileage_return = ?, return_time = ?, miles_used = ?, status = 'completed', updated_at = SYSUTCDATETIME()
      WHERE id = ?
    """, (mileage_return, return_time, miles_used, trip_id))
    cur.execute("SELECT last_service_mileage FROM dbo.vehicles WHERE id = ?", (vehicle_id,))
    v_row = cur.fetchone()
    last_service_mileage = v_row[0] if v_row else None
    cur.execute("UPDATE dbo.vehicles SET current_mileage = ?, updated_at = SYSUTCDATETIME() WHERE id = ?", (mileage_return, vehicle_id))
    if last_service_mileage is not None:
        new_until = 4000 - (mileage_return - last_service_mileage)
        cur.execute("UPDATE dbo.vehicles SET miles_until_service = ? WHERE id = ?", (new_until, vehicle_id))
    cur.execute("UPDATE dbo.vehicles SET status='motorpool' WHERE id = ?", (vehicle_id,))
    conn.commit()
    conn.close()

def create_service_log(payload):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
      INSERT INTO dbo.service_logs (vehicle_id, service_center, date_of_service, work_performed,
                                    dropped_off_by, picked_up_by, cost, receipt_file_url, notes, created_by, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME())
    """, (
        payload['vehicle_id'],
        payload.get('service_center'),
        payload.get('date_of_service'),
        payload.get('work_performed'),
        payload.get('dropped_off_by'),
        payload.get('picked_up_by'),
        payload.get('cost'),
        payload.get('receipt_file_url'),
        payload.get('notes'),
        payload.get('created_by')
    ))
    cur.execute("SELECT current_mileage FROM dbo.vehicles WHERE id = ?", (payload['vehicle_id'],))
    cm_row = cur.fetchone()
    cm = cm_row[0] if cm_row else None
    if cm is not None:
        cur.execute("UPDATE dbo.vehicles SET last_service_mileage = ?, last_service_date = ?, miles_until_service = 4000, updated_at = SYSUTCDATETIME() WHERE id = ?",
                    (cm, payload.get('date_of_service'), payload['vehicle_id']))
    conn.commit()
    conn.close()

def fetch_active_trips():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
      SELECT t.id, t.vehicle_id, t.driver_name, t.driver_phone, t.driver_email, t.work_location, t.destination, t.purpose, t.departure_time, t.mileage_departure
      FROM dbo.trip_logs t
      WHERE t.status = 'active'
      ORDER BY t.departure_time DESC
    """)
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return rows

def generate_advanced_report(start_date=None, end_date=None, location=None, vehicle_id=None, driver_name=None, status=None):
    conn = get_conn()
    cur = conn.cursor()
    q = """
    SELECT t.id AS trip_id, t.vehicle_id, v.make_model, v.license_plate, t.driver_name, t.driver_phone, t.driver_email,
           t.work_location, t.destination, t.purpose, t.departure_time, t.return_time, t.mileage_departure, t.mileage_return, t.miles_used, t.status
    FROM dbo.trip_logs t
    JOIN dbo.vehicles v ON v.id = t.vehicle_id
    WHERE 1=1
    """
    params = []
    if start_date:
        q += " AND t.departure_time >= ?"
        params.append(start_date)
    if end_date:
        q += " AND t.return_time <= ?"
        params.append(end_date)
    if location:
        q += " AND t.work_location = ?"
        params.append(location)
    if vehicle_id:
        q += " AND t.vehicle_id = ?"
        params.append(vehicle_id)
    if driver_name:
        q += " AND t.driver_name LIKE ?"
        params.append(f"%{{driver_name}}%")
    if status:
        q += " AND t.status = ?"
        params.append(status)
    q += " ORDER BY t.departure_time DESC"
    cur.execute(q, params)
    cols = [c[0] for c in cur.description]
    rows = [list(r) for r in cur.fetchall()]
    conn.close()
    df = pd.DataFrame(rows, columns=cols)
    return df
