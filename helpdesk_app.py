"""
Main entry for VDH HelpDesk + Fleet integration.

This wrapper exposes a sidebar navigation that lets you switch between:
- the existing Helpdesk UI (if present),
- and the Fleet Management UI implemented under fleet/.

It detects the existing helpdesk module safely (ImportError fallback).
"""
import streamlit as st

# Try to import existing helpdesk page (if the project provides a helpdesk module)
try:
    # If your helpdesk UI is a function or module, adapt the import below.
    # Common patterns:
    #  - from helpdesk import run as helpdesk_run
    #  - from helpdesk import helpdesk_page
    # If none exists, the fallback helpdesk_main() below will display a placeholder.
    from helpdesk import helpdesk_page as helpdesk_main  # try canonical import
except Exception:
    try:
        from helpdesk_app_core import main as helpdesk_main  # alternate name if present
    except Exception:
        def helpdesk_main():
            st.header("VDH Helpdesk")
            st.info("Helpdesk UI is not available (placeholder).")
            st.markdown(
                "If you have an existing helpdesk module, export a function named "
                "`helpdesk_page` or `main` and update the import at the top of this file."
            )

# Import fleet UI from the existing fleet package. This package already exists in the repo
# (fleet/fleet_ui.py). The function used here is fleet_page().
from fleet import fleet_ui

def app_config():
    st.set_page_config(page_title="VDH Helpdesk + Fleet", layout="wide")

def main():
    app_config()
    st.sidebar.title("VDH App")
    st.sidebar.markdown("Navigation")
    page = st.sidebar.radio("Go to", ["Helpdesk", "Fleet Management", "Admin / Tools"])

    # Optional debug toggle
    debug = st.sidebar.checkbox("Debug logging", value=False)
    if debug:
        st.sidebar.caption("Debug mode ON")

    if page == "Helpdesk":
        # Call the detected helpdesk entrypoint
        try:
            helpdesk_main()
        except Exception as e:
            st.error(f"Helpdesk UI failed to load: {e}")
    elif page == "Fleet Management":
        # fleet_page() is implemented in fleet/fleet_ui.py and uses st.secrets["database"]
        try:
            fleet_ui.fleet_page()
        except Exception as e:
            st.error(f"Fleet UI failed to load: {e}")
            st.exception(e)
    else:
        st.header("Admin / Tools")
        st.markdown("Useful admin tasks for operators and developers:")
        st.write("- Verify DB connection: try `from fleet import fleet_db; fleet_db.fetch_vehicles()` in a console")
        st.write("- Confirm `st.secrets['database']` is configured in Streamlit Cloud")
        st.write("- Run DB migrations on staging before production")

if __name__ == "__main__":
    main()
