# show_conn_str.py
import streamlit as st

db = st.secrets["database"]

server = db.get("server", "")
if not server.lower().startswith("tcp:") and "," not in server:
    server = f"tcp:{server},1433"

driver = "ODBC Driver 18 for SQL Server"
masked_pwd = "*****"  # we won't print the real password
conn_str = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={db.get('database')};"
    f"UID={db.get('username')};"
    f"PWD={masked_pwd};"
    "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)
print("Constructed (masked) connection string:")
print(conn_str)