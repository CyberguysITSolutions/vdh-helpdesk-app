import streamlit as st
from fleet import fleet_db
import pandas as pd
from datetime import datetime

LOCATIONS = [
    "Chesapeake", "Richmond", "Norfolk", "Roanoke", "Harrisonburg", "Charlottesville", "Alexandria"
]

def vehicle_select_list():
    st.subheader("Available Vehicles")
    vehicles = fleet_db.fetch_vehicles(order_by_usage=True)
    if not vehicles:
        st.info("No vehicles registered.")
        return None
    cols = st.columns(3)
    for i, v in enumerate(vehicles):
        col = cols[i % 3]
        is_overdue = v.get('miles_until_service') is not None and v['miles_until_service'] <= 0
        with col:
            if v.get('photo_url'):
                st.image(v['photo_url'], width=150)
            label = f"{{v['make_model']}} ({{v['license_plate']}})"
            if is_overdue:
                st.button(f"{{label}} — Overdue for service", key=f"veh_{{v['id']}}", disabled=True)
            else:
                if st.button(label, key=f"veh_btn_{{v['id']}}"):
                    st.session_state['selected_vehicle'] = v['id']
    return st.session_state.get('selected_vehicle')

def sign_out_form():
    st.header("Sign Out Vehicle")
    vehicle_id = st.session_state.get('selected_vehicle')
    if not vehicle_id:
        st.warning("Select a vehicle from the list first.")
        return
    with st.form("signout"):
        st.markdown("Fill driver and trip details")
        driver_name = st.text_input("Driver name")
        driver_phone = st.text_input("Driver phone")
        driver_email = st.text_input("Driver email")
        work_location = st.selectbox("Work location (VDH site)", options=LOCATIONS)
        destination = st.text_input("Destination")
        purpose = st.text_area("Purpose")
        departure_time = st.datetime_input("Departure time", value=datetime.utcnow())
        mileage_departure = st.number_input("Mileage at Departure", min_value=0, step=1)
        submitted = st.form_submit_button("Sign Out")
    if submitted:
        payload = {
            'vehicle_id': vehicle_id,
            'driver_name': driver_name,
            'driver_phone': driver_phone,
            'driver_email': driver_email,
            'work_location': work_location,
            'destination': destination,
            'purpose': purpose,
            'departure_time': departure_time,
            'mileage_departure': int(mileage_departure)
        }
        try:
            fleet_db.create_trip(payload)
            st.success("Vehicle signed out.")
        except Exception as e:
            st.error(f"Failed to sign out vehicle: {{e}}")

def return_form():
    st.header("Return Vehicle")
    trips = fleet_db.fetch_active_trips()
    if not trips:
        st.info("No active trips.")
        return
    options = {f"#{{t['id']}} - Veh {{t['vehicle_id']}} - {{t['driver_name']}} ({{t['work_location']}})": t['id'] for t in trips}
    choice = st.selectbox("Active trips", options=list(options.keys()))
    trip_id = options[choice]
    mileage_return = st.number_input("Mileage upon return", min_value=0, step=1)
    return_time = st.datetime_input("Return time", value=datetime.utcnow())
    if st.button("Complete Return"):
        try:
            fleet_db.complete_trip(trip_id, int(mileage_return), return_time)
            st.success("Trip completed and vehicle updated.")
        except Exception as e:
            st.error(f"Failed to complete return: {{e}}")

def admin_dashboard():
    st.header("Fleet Admin Dashboard")
    vehicles = fleet_db.fetch_vehicles(order_by_usage=False)
    df = pd.DataFrame(vehicles)
    if df.empty:
        st.info("No vehicles to display.")
        return
    counts = df['status'].value_counts().to_dict()
    st.metric("Motorpool", counts.get('motorpool', 0))
    st.metric("Dispatched", counts.get('dispatched', 0))
    st.metric("Maintenance", counts.get('maintenance', 0))
    st.metric("Out of Service", counts.get('out_of_service', 0))
    st.markdown("---")
    df_display = df[['id', 'make_model', 'license_plate', 'current_mileage', 'miles_until_service', 'status', 'miles_per_month']]
    st.dataframe(df_display.sort_values('miles_per_month', ascending=True))
    st.markdown("Dispatched vehicles (active trips):")
    trips = fleet_db.fetch_active_trips()
    if trips:
        tdf = pd.DataFrame(trips)
        st.dataframe(tdf[['id','vehicle_id','driver_name','driver_phone','driver_email','work_location','destination','purpose','departure_time']])
    else:
        st.info("No dispatched vehicles.")

def reports_ui():
    st.header("Advanced Fleet Reports")
    with st.form("report_form"):
        from_date = st.date_input("From date")
        to_date = st.date_input("To date")
        loc = st.selectbox("Work location (optional)", options=["All"] + LOCATIONS)
        vehicle_id = st.text_input("Vehicle ID (optional)")
        driver_name = st.text_input("Driver name contains (optional)")
        status = st.selectbox("Trip status (optional)", options=["All", "active", "completed", "cancelled"])
        submitted = st.form_submit_button("Generate Report")
    if submitted:
        location = None if loc == "All" else loc
        v_id = int(vehicle_id) if vehicle_id.strip().isdigit() else None
        st.info("Generating report...")
        df = fleet_db.generate_advanced_report(start_date=from_date, end_date=to_date, location=location, vehicle_id=v_id, driver_name=driver_name or None, status=None if status=="All" else status)
        st.success(f"Report generated: {{len(df)}} rows")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download CSV", data=csv, file_name="fleet_report.csv", mime="text/csv")
