# Simple Streamlit test page to verify Streamlit pages detection
import streamlit as st

st.title("TEST PAGE - pages/99_test_page.py")
st.write("If you can see this, Streamlit successfully discovered pages/99_test_page.py.")
st.write("This is a plain test. No DB access or dependencies.")
st.button("OK, I see this")