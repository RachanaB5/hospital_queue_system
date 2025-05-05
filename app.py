import streamlit as st
import requests

st.set_page_config(page_title="Hospital Triage System", layout="wide")
st.title("🏥 Hospital Triage Queue Management")

backend_url = "http://localhost:5000"

# ─────────────────────────────────────────────
# Sidebar – App Info & Patient History
# ─────────────────────────────────────────────
st.sidebar.header("📋 Dashboard")
st.sidebar.markdown("Manage patient queue based on severity.")

# Fetch patient history from backend
with st.sidebar.expander("📜 Patient History", expanded=False):
    history = requests.get(f"{backend_url}/history").json()
    if history:
        for p in history:
            st.markdown(f"✅ **{p['name']}** - {p['condition']} (Severity: {p['severity']})")
    else:
        st.info("No patient history yet.")

# Admin actions
st.sidebar.header("⚙️ Admin Tools")
if st.sidebar.button("🔁 Refresh Queue"):
    st.rerun()  # <-- fixed here

# ─────────────────────────────────────────────
# Patient Form (Main Area)
# ─────────────────────────────────────────────
st.subheader("➕ Add New Patient to Triage Queue")
with st.form("add_patient_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Patient Name")
        condition = st.text_input("Condition (e.g., Chest Pain, Fever)")
    with col2:
        severity = st.selectbox(
            "Severity Level",
            [1, 2, 3],
            format_func=lambda x: {1: "Critical (1)", 2: "Serious (2)", 3: "Stable (3)"}[x]
        )
    submitted = st.form_submit_button("🚑 Add to Queue")

    if submitted:
        res = requests.post(f"{backend_url}/add_patient", json={
            "name": name,
            "condition": condition,
            "severity": severity
        })
        if res.status_code == 200:
            st.success("✅ Patient added to queue.")
        else:
            st.error("❌ Failed to add patient.")

# ─────────────────────────────────────────────
# Queue Display
# ─────────────────────────────────────────────
st.subheader("🧾 Current Triage Queue")
queue = requests.get(f"{backend_url}/view_queue").json()
if queue:
    for i, p in enumerate(queue, start=1):
        st.write(f"**{i}.** 🧑‍⚕️ {p['name']} - {p['condition']} (Severity: {p['severity']})")
else:
    st.info("Queue is currently empty.")

# ─────────────────────────────────────────────
# Call Next Patient
# ─────────────────────────────────────────────
st.subheader("📣 Call Next Patient")
if st.button("Call Next Patient"):
    res = requests.get(f"{backend_url}/next_patient")
    if res.status_code == 200:
        next_p = res.json()
        st.success(f"🆕 **Next Patient:** {next_p['name']} - {next_p['condition']} (Severity: {next_p['severity']})")
    else:
        st.warning("No patients in the queue.")
    
