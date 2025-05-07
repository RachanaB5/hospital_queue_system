import streamlit as st
import requests
import datetime
import pandas as pd
import time

st.set_page_config(page_title="Hospital Triage System", layout="wide")
st.title("🏥 Hospital Triage Queue Management")

backend_url = "http://localhost:5002"

# ─────────────────────────────────────────────
# Enhanced Custom CSS Styling
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif !important;
    }

    .main > div {
        background: #ffffff;
        padding: 30px;
        border-radius: 18px;
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.08);
        margin-bottom: 25px;
    }

    .stButton>button {
        background: linear-gradient(90deg, #2563eb, #1e40af);
        color: white;
        font-weight: 600;
        padding: 0.75em 1.5em;
        border-radius: 14px;
        transition: all 0.3s ease;
        border: none;
        box-shadow: 0 4px 8px rgba(0,0,0,0.12);
    }

    .stButton>button:hover {
        background: linear-gradient(90deg, #1e40af, #2563eb);
        transform: scale(1.03);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
    }

    .patient-card {
        background: #f9fafb;
        color: black;
        padding: 18px 24px;
        border-radius: 16px;
        margin-bottom: 16px;
        border-left: 5px solid var(--primary);
        transition: 0.3s;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    }

    .patient-card:hover {
        transform: scale(1.01);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
    }

    .severity-badge {
        font-size: 0.8em;
        padding: 5px 12px;
        border-radius: 999px;
        font-weight: 600;
        margin-left: 10px;
        color: white;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }

    .severity-1 {
        background: #dc2626;
    }
    .severity-2 {
        background: #f59e0b;
    }
    .severity-3 {
        background: #10b981;
    }

    .next-patient-banner {
        background: linear-gradient(90deg, #3b82f6, #2563eb);
        color: white;
        padding: 24px;
        border-radius: 20px;
        font-size: 1.2em;
        text-align: center;
        animation: pulse 2s infinite;
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }

    .history-item {
        background: #f9fafb;
        color: black;
        border-left: 4px solid #2563eb;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-radius: 10px;
    }

    .timestamp {
        font-size: 0.75em;
        color: #64748b;
        margin-top: 5px;
    }

    .wait-time {
        font-size: 0.85em;
        font-weight: 600;
        color: #1e40af;
    }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }

</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────
def calculate_wait_time(patient, queue):
    """Calculate dynamic wait time based on position in queue and severity"""
    base_times = {1: 15, 2: 10, 3: 5}  # Base minutes per severity level
    position = queue.index(patient) + 1
    
    # Calculate wait time based on patients ahead in queue
    ahead_patients = queue[:position-1]
    wait_time = sum(base_times.get(p['severity'], 5) for p in ahead_patients)
    
    # Add base time for current patient
    wait_time += base_times.get(patient['severity'], 5)
    
    # Ensure minimum wait time
    return max(5, wait_time)

def get_current_time():
    """Get current time in HH:MM:SS format"""
    return datetime.datetime.now().strftime("%H:%M:%S")

# ─────────────────────────────────────────────
# Sidebar – App Info & Patient History
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="color: white; font-size: 28px;">🏥 Triage Dashboard</h1>
            <p style="color: rgba(255,255,255,0.8);">Real-time patient queue management</p>
        </div>
    """, unsafe_allow_html=True)

    # Current time display
    st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px; padding: 10px; 
                    background: rgba(255,255,255,0.1); border-radius: 10px;">
            <div style="font-size: 1.2em; font-weight: bold;">🕒 Current Time</div>
            <div>{get_current_time()}</div>
        </div>
    """, unsafe_allow_html=True)

    # Admin tools
    with st.expander("⚙️ Admin Tools", expanded=True):
        if st.button("🔄 Refresh Queue", key="refresh_btn"):
            st.rerun()
        if st.button("📊 Generate Report", key="report_btn"):
            history = requests.get(f"{backend_url}/history").json()
            if history:
                report_data = [
                    {
                        "Name": p['name'],
                        "Condition": p['condition'],
                        "Severity": p['severity'],
                        "Timestamp": p.get('arrival_time', 'N/A'),
                        "Status": "Completed"
                    }
                    for p in history
                ]
                df = pd.DataFrame(report_data)
                st.download_button(
                    "⬇️ Download Patient Report (CSV)", 
                    df.to_csv(index=False).encode(), 
                    file_name=f"patient_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
            else:
                st.info("No patient data to generate report.")

    # Patient history
    with st.expander("📜 Patient History", expanded=True):
        history = requests.get(f"{backend_url}/history").json()
        if history:
            for p in history:
                st.markdown(f"""
                    <div class="history-item">
                        <div style="font-weight: bold;">{p['name']}</div>
                        <div style="font-size: 0.85em; opacity: 0.9;">{p['condition']}</div>
                        <span class="severity-badge severity-{p['severity']}">Severity {p['severity']}</span>
                        <div class="timestamp">Arrived: {p.get('arrival_time', 'N/A')}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No patient history yet.")

# ─────────────────────────────────────────────
# Patient Form
# ─────────────────────────────────────────────
st.subheader("➕ Add New Patient to Triage Queue")
with st.form("add_patient_form"):
    st.markdown('<div class="form-container">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Patient Full Name", placeholder="John Smith")
        condition = st.text_input("Medical Condition", placeholder="Chest pain, fever, etc.")
    with col2:
        severity = st.selectbox(
            "Severity Level",
            [1, 2, 3],
            format_func=lambda x: {1: "🚨 Critical (1)", 2: "⚠️ Serious (2)", 3: "✅ Stable (3)"}[x]
        )
        arrival_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.markdown(f"""
            <div style="margin-top: 10px;">
                <div style="font-size: 0.9em; color: #64748b;">Arrival Time:</div>
                <div style="font-weight: bold;">{arrival_time}</div>
            </div>
        """, unsafe_allow_html=True)

    submitted = st.form_submit_button("🚑 Add to Queue", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        if not name or not condition:
            st.error("Please fill in all required fields")
        else:
            res = requests.post(f"{backend_url}/add_patient", json={
                "name": name,
                "condition": condition,
                "severity": severity,
                "arrival_time": arrival_time
            })
            if res.status_code == 200:
                st.success("✅ Patient successfully added to queue!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Failed to add patient. Please try again.")

# ─────────────────────────────────────────────
# Queue Display
# ─────────────────────────────────────────────
st.subheader("🧾 Current Triage Queue")
queue = requests.get(f"{backend_url}/view_queue").json()

if queue:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.metric("Total Patients in Queue", len(queue))

    for i, p in enumerate(queue, start=1):
        emoji = "🚨" if p['severity'] == 1 else "⚠️" if p['severity'] == 2 else "✅"
        wait_time = calculate_wait_time(p, queue)
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"""
                <div class="patient-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="font-size: 1.1em;">{emoji} {i}. {p['name']}</strong>
                            <div style="color: #64748b; font-size: 0.9em;">{p['condition']}</div>
                        </div>
                        <span class="severity-badge severity-{p['severity']}">Priority {p['severity']}</span>
                    </div>
                    <div style="margin-top: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div style="font-size: 0.8em; color: #64748b;">
                            Arrived: {p.get('arrival_time', 'N/A')}
                        </div>
                        <div class="wait-time">
                            Estimated wait: ~{wait_time} minutes
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("✅ Mark as Treated", key=f"treated_{i}"):
                response = requests.post(f"{backend_url}/mark_treated", json={"name": p['name']})
                if response.status_code == 200:
                    st.success(f"{p['name']} marked as treated.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to update status. Please try again.")
else:
    st.info("🎉 The queue is currently empty! No patients waiting.")

# ─────────────────────────────────────────────
# Call Next Patient
# ─────────────────────────────────────────────
st.subheader("📣 Call Next Patient")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔔 Call Next Patient", type="primary", key="next_patient_btn"):
        res = requests.get(f"{backend_url}/next_patient")
        if res.status_code == 200:
            next_p = res.json()
            st.markdown(f"""
                <div class="next-patient-banner">
                    <h3>Now Serving</h3>
                    <h2>{next_p['name']}</h2>
                    <p>{next_p['condition']} • Severity: {next_p['severity']}</p>
                    <div style="font-size: 0.9em; margin-top: 10px;">
                        Arrived at: {next_p.get('arrival_time', 'N/A')}
                    </div>
                    <div style="font-size: 0.9em; margin-top: 5px;">
                        Called at: {get_current_time()}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("No patients in the queue to call.")
