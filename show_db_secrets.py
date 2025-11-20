import streamlit as st
try:
    db = st.secrets["database"]
    print("server:", db.get("server"))
    print("database:", db.get("database"))
    print("username:", db.get("username"))
    pwd = db.get("password")
    print("password set:", bool(pwd))
except Exception as e:
    print("Could not read st.secrets['database']:", e)