import streamlit as st
from fleet import fleet_db

def reports_ui():
    st.header("Advanced Fleet Reports")
    with st.form("report_form"):
        from_date = st.date_input("From date")
        to_date = st.date_input("To date")
        location = st.text_input("Work location (optional)")
        vehicle_id = st.text_input("Vehicle ID (optional)")
        driver_name = st.text_input("Driver name contains (optional)")
        status = st.selectbox("Trip status (optional)", options=["All", "active", "completed", "cancelled"])
        submitted = st.form_submit_button("Generate Report")
    if submitted:
        v_id = int(vehicle_id) if vehicle_id.strip().isdigit() else None
        df = fleet_db.generate_advanced_report(start_date=from_date, end_date=to_date, location=location or None, vehicle_id=v_id, driver_name=driver_name or None, status=None if status=="All" else status)
        st.success(f"Report generated: {{len(df)}} rows")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(label="Download CSV", data=csv, file_name="fleet_report.csv", mime="text/csv")
