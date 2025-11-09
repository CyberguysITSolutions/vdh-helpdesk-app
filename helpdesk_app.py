#!/usr/bin/env python3
"""
VDH Helpdesk application with Fleet Management integration.

This file intentionally attempts to import the existing helpdesk UI
(if available) and integrates the fleet UI under fleet.fleet_ui.

Usage:
  streamlit run helpdesk_app.py
"""
import streamlit as st
import traceback

# Try to import the existing helpdesk UI entrypoint from whatever module name is present.
# Common patterns in this repo are:
#  - an exported function named `helpdesk_page` or `main` in a helpdesk module
#  - a top-level helpdesk_app.py that defines a callable main() or app()
_helpdesk_loaded = False
helpdesk_main = None

# Try several likely imports; adapt if your helpdesk UI is under a different symbol.
try:
    # First try a package module `helpdesk` exposing a function helpdesk_page
    from helpdesk import helpdesk_page as helpdesk_main  # type: ignore
    _helpdesk_loaded = True
except Exception:
    try:
        # Try an alternate module name
        from helpdesk_app_core import main as helpdesk_main  # type: ignore
        _helpdesk_loaded = True
    except Exception:
        try:
            # Some repos ship the helpdesk logic in the top-level helpdesk_app.py as a function main()
            # We'll attempt a dynamic import fallback — import by filename (if present).
            import importlib.util
            import pathlib
            p = pathlib.Path(__file__).parent / "helpdesk_app.py"
            # If this file is itself being replaced, skip trying to import itself
            if p.exists() and p.resolve() != pathlib.Path(__file__).resolve():
                spec = importlib.util.spec_from_file_location("helpdesk_app_local", str(p))
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)  # type: ignore
                    # prefer a function named helpdesk_page or main
                    if hasattr(module, "helpdesk_page"):
                        helpdesk_main = getattr(module, "helpdesk_page")
                        _helpdesk_loaded = True
                    elif hasattr(module, "main"):
                        helpdesk_main = getattr(module, "main")
                        _helpdesk_loaded = True
        except Exception:
            _helpdesk_loaded = False

# Import fleet UI (implemented in fleet/fleet_ui.py)
try:
    from fleet import fleet_ui
    _fleet_available = True
except Exception:
    fleet_ui = None  # type: ignore
    _fleet_available = False

def app_config():
    st.set_page_config(page_title="VDH Helpdesk + Fleet", layout="wide")

def show_helpdesk_placeholder():
    st.header("VDH Helpdesk")
    st.info("Helpdesk UI not detected or failed to import.")
    st.markdown(
        "If you have an existing helpdesk module, expose a function named "
        "`helpdesk_page` or `main` and update this file's import to point at it."
    )

def admin_tools():
    st.header("Admin / Tools")
    st.markdown("Utilities for operators and maintainers.")
    st.write("- Verify DB connection from the fleet module (if configured).")
    st.write("- Inspect secrets: do not print secrets — use checks that attempt connections only.")
    if st.button("Show loaded modules (debug)"):
        modules = sorted([m for m in list(sys.modules.keys()) if m.startswith("fleet") or m.startswith("helpdesk")])
        st.write(modules)

def main():
    app_config()
    st.sidebar.title("VDH App")
    st.sidebar.markdown("Navigation")
    pages = ["Helpdesk"]
    if _fleet_available:
        pages.append("Fleet Management")
    pages.append("Admin / Tools")

    page = st.sidebar.radio("Go to", pages)
    debug = st.sidebar.checkbox("Debug logging", value=False)

    if page == "Helpdesk":
        if _helpdesk_loaded and helpdesk_main is not None:
            try:
                helpdesk_main()
            except Exception as e:
                st.error("Helpdesk UI failed to load. See error below.")
                if debug:
                    st.text(traceback.format_exc())
                else:
                    st.error(str(e))
                    st.markdown("Enable Debug logging in the sidebar to see a full traceback.")
        else:
            show_helpdesk_placeholder()

    elif page == "Fleet Management":
        if _fleet_available and fleet_ui is not None:
            try:
                # fleet_page() is expected to handle DB connection via st.secrets["database"]
                fleet_ui.fleet_page()
            except Exception as e:
                st.error("Fleet UI failed to load. See error below.")
                if debug:
                    st.text(traceback.format_exc())
                else:
                    st.error(str(e))
                    st.markdown("Enable Debug logging in the sidebar to see a full traceback.")
        else:
            st.error("Fleet feature not available in this deployment. Ensure fleet/ package files are present.")

    else:  # Admin / Tools
        admin_tools()

if __name__ == "__main__":
    import sys
    main()
