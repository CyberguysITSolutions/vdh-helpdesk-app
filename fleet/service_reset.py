import streamlit as st
from fleet import fleet_db
from azure.storage.blob import BlobServiceClient
import uuid

def upload_receipt_to_blob(file_obj):
    blob_conf = st.secrets.get("blob")
    if not blob_conf:
        return None
    bsc = BlobServiceClient(account_url=f"https://{{blob_conf['account_name']}}.blob.core.windows.net", credential=blob_conf['key'])
    container = blob_conf.get('container', 'receipts')
    blob_name = f"receipts/{{uuid.uuid4()}}-{{file_obj.name}}"
    blob_client = bsc.get_blob_client(container=container, blob=blob_name)
    blob_client.upload_blob(file_obj.getvalue(), overwrite=True)
    return blob_client.url

def reset_service_ui(vehicle_id):
    st.header("Reset Miles Until Next Service")
    with st.form("reset_service"):
        service_center = st.text_input("Service Center")
        date_of_service = st.date_input("Date of Last Service")
        work_performed = st.text_area("Work Performed")
        dropped_off_by = st.text_input("Who dropped off the vehicle?")
        picked_up_by = st.text_input("Who picked up the vehicle?")
        cost = st.number_input("Cost", min_value=0.0, format="%.2f")
        receipt = st.file_uploader("Receipt (optional)", type=["pdf","jpg","png"])
        notes = st.text_area("Notes / Log")
        submitted = st.form_submit_button("Submit Service Log and Reset")
    if submitted:
        receipt_url = None
        if receipt:
            try:
                receipt_url = upload_receipt_to_blob(receipt)
            except Exception as e:
                st.warning(f"Receipt upload failed: {{e}}. Proceeding without receipt.")
        payload = {
            'vehicle_id': vehicle_id,
            'service_center': service_center,
            'date_of_service': date_of_service,
            'work_performed': work_performed,
            'dropped_off_by': dropped_off_by,
            'picked_up_by': picked_up_by,
            'cost': cost if cost > 0 else None,
            'receipt_file_url': receipt_url,
            'notes': notes,
            'created_by': st.session_state.get('user_id')
        }
        try:
            fleet_db.create_service_log(payload)
            st.success("Service log created and miles reset.")
        except Exception as e:
            st.error(f"Failed to create service log: {{e}}")
