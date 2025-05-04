import streamlit as st
import requests

st.title("🏥 Hospital Triage Queue Management")

backend_url = "http://localhost:5000"

# Add patient form
with st.form("add_patient_form"):
    name = st.text_input("Patient Name")
    condition = st.text_input("Condition (e.g., Chest Pain, Fever)")
    severity = st.selectbox("Severity Level", [1, 2, 3], format_func=lambda x: {1: "Critical", 2: "Serious", 3: "Stable"}[x])
    submitted = st.form_submit_button("Add to Queue")

    if submitted:
        res = requests.post(f"{backend_url}/add_patient", json={
            "name": name,
            "condition": condition,
            "severity": severity
        })
        st.success("Patient added to queue.")

# View queue
st.subheader("🧾 Current Triage Queue")
queue = requests.get(f"{backend_url}/view_queue").json()
for p in queue:
    st.write(f"🧑‍⚕️ {p['name']} - {p['condition']} (Severity: {p['severity']})")

# Call next patient
if st.button("Call Next Patient"):
    res = requests.get(f"{backend_url}/next_patient")
    if res.status_code == 200:
        next_p = res.json()
        st.success(f"Next Patient: {next_p['name']} - {next_p['condition']}")
    else:
        st.warning("No patients in the queue.")
