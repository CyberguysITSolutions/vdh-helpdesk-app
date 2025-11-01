"""
helpdesk_app.py

Full application entrypoint that integrates the existing Helpdesk UI with the Fleet Management UI.
This file expects the repo to include a `fleet` package with the modules:
 - fleet.fleet_ui
 - fleet.service_reset
 - fleet.reports_ui

It also expects Streamlit secrets to include database and optional blob storage connection info
under st.secrets["database"] and st.secrets["blob"].

Usage:
  streamlit run helpdesk_app.py

Behavior:
  - Top-level navigation: Helpdesk | Fleet | Settings
  - Fleet has subpages: Overview, Sign Out, Return, Admin - Service Reset, Reports
  - If fleet modules are missing, the app displays a clear placeholder and does not crash.

Note: This file is standalone and intended to be pasted/overwritten into your repo root.
"""

from typing import Optional
import streamlit as st

# Try importing fleet submodules; if they don't exist show informative fallback pages.
try:
    from fleet import fleet_ui as fleet_ui_module
except Exception:
    fleet_ui_module = None

try:
    from fleet import service_reset as service_reset_module
except Exception:
    service_reset_module = None

try:
    from fleet import reports_ui as reports_ui_module
except Exception:
    reports_ui_module = None

# --- Utilities ---------------------------------------------------------------

def get_db_config():
    """Return database config from Streamlit secrets or None."""
    try:
        return st.secrets["database"]
    except Exception:
        return None

def show_missing_module_message(module_name: str):
    st.warning(f"The optional module '{module_name}' was not found in the repo. "
               "Ensure the fleet package contains this module, or run the app without that feature.")

# --- Helpdesk placeholder UI -------------------------------------------------

def render_helpdesk_home():
    st.title("VDH Helpdesk")
    st.markdown(
        "This is the Helpdesk entry page. Use the sidebar to navigate between Helpdesk and Fleet features."
    )

    st.subheader("Quick actions")
    st.button("Create ticket (placeholder)")
    st.button("View open tickets (placeholder)")
    st.info("Replace these placeholders with your real Helpdesk functionality as needed.")

# --- Fleet navigation & wrappers ---------------------------------------------

def fleet_overview():
    st.header("Fleet Overview")
    db_cfg = get_db_config()
    if db_cfg is None:
        st.error("No database configuration found in Streamlit secrets (st.secrets['database']). "
                 "Please add DB connection info before testing Fleet features.")
        return

    if fleet_ui_module and hasattr(fleet_ui_module, "overview"):
        return fleet_ui_module.overview(db_cfg)
    else:
        show_missing_module_message("fleet.fleet_ui")
        st.write("Overview: sample placeholders")
        st.metric("Vehicles", "N/A")
        st.metric("Overdue for service", "N/A")


def fleet_sign_out():
    st.header("Vehicle Sign Out")
    if fleet_ui_module and hasattr(fleet_ui_module, "sign_out_form"):
        return fleet_ui_module.sign_out_form()
    else:
        show_missing_module_message("fleet.fleet_ui")
        st.info("Sign Out form placeholder")
        driver = st.text_input("Driver name")
        vehicle_id = st.text_input("Vehicle ID")
        if st.button("Sign Out (simulate)"):
            st.success(f"Simulated sign out for driver {driver} and vehicle {vehicle_id}")


def fleet_return():
    st.header("Vehicle Return")
    if fleet_ui_module and hasattr(fleet_ui_module, "return_form"):
        return fleet_ui_module.return_form()
    else:
        show_missing_module_message("fleet.fleet_ui")
        st.info("Return form placeholder")
        vehicle_id = st.text_input("Vehicle ID (return)")
        mileage = st.number_input("Return mileage", min_value=0, format="%d")
        if st.button("Complete Return (simulate)"):
            st.success(f"Simulated return for vehicle {vehicle_id} with mileage {mileage}")


def fleet_service_reset_admin():
    st.header("Service Reset (Admin)")
    if service_reset_module and hasattr(service_reset_module, "reset_service_ui"):
        return service_reset_module.reset_service_ui()
    else:
        show_missing_module_message("fleet.service_reset")
        st.info("Service reset placeholder")
        vehicle_id = st.text_input("Vehicle ID (service reset)")
        new_last_service_mileage = st.number_input("New last service mileage", min_value=0, format="%d")
        if st.button("Record Service (simulate)"):
            st.success(f"Simulated service reset for vehicle {vehicle_id} to {new_last_service_mileage} miles")


def fleet_reports():
    st.header("Fleet Reports")
    if reports_ui_module and hasattr(reports_ui_module, "reports_ui"):
        return reports_ui_module.reports_ui()
    else:
        show_missing_module_message("fleet.reports_ui")
        st.info("Reports placeholder")
        if st.button("Export CSV (simulate)"):
            st.success("Simulated CSV generated. (Replace with real export in reports_ui.)")


# --- Main app ----------------------------------------------------------------

def main():
    st.set_page_config(page_title="VDH Helpdesk + Fleet", layout="wide")

    # Top-level navigation
    with st.sidebar:
        st.title("VDH App")
        app_section = st.radio("Select app", ("Helpdesk", "Fleet", "Settings"), index=0)

        if app_section == "Fleet":
            fleet_page = st.selectbox("Fleet pages", ["Overview", "Sign Out", "Return", "Admin - Service Reset", "Reports"])
        else:
            fleet_page = None

        st.markdown("---")
        st.caption("App version: integrated-fleet-1.0")

    # Render content for each top-level area
    if app_section == "Helpdesk":
        render_helpdesk_home()

    elif app_section == "Fleet":
        # Quick DB info show for convenience
        db_cfg = get_db_config()
        if db_cfg:
            st.sidebar.success("DB config found")
        else:
            st.sidebar.warning("No DB config found in st.secrets['database']")

        if fleet_page == "Overview":
            fleet_overview()
        elif fleet_page == "Sign Out":
            fleet_sign_out()
        elif fleet_page == "Return":
            fleet_return()
        elif fleet_page == "Admin - Service Reset":
            fleet_service_reset_admin()
        elif fleet_page == "Reports":
            fleet_reports()
        else:
            st.info("Select a Fleet page from the left.")

    elif app_section == "Settings":
        st.header("Settings")
        st.write("Streamlit secrets preview (masked):")
        try:
            st.json({k: ("***" if isinstance(v, str) and len(str(v)) > 0 else v) for k, v in st.secrets.items()})
        except Exception:
            st.write("No secrets loaded.")

    else:
        st.error("Unknown app section selected.")

if __name__ == "__main__":
    main()
