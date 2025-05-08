import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import time
import pytz


st.set_page_config(page_title="Hospital Triage System", layout="wide")
st.title("🏥 Hospital Triage Queue Management")

backend_url = "https://hospital-queue-system.onrender.com"  # Change this to your deployed backend URL when needed

# ─────────────────────────────────────────────
# Caching and API Safety functions
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)  # Cache for 5 minutes
def safe_api_call(url, method="get", json_data=None):
    """Make API calls with error handling and caching"""
    try:
        if method.lower() == "get":
            response = requests.get(url, timeout=10)
        elif method.lower() == "post":
            response = requests.post(url, json=json_data, timeout=10)
        else:
            return {"error": "Invalid method"}
            
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API returned status code {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    except ValueError:
        return {"error": "Invalid response from API"}

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_queue_data():
    """Get and cache the queue data"""
    return safe_api_call(f"{backend_url}/view_queue")

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_history_data():
    """Get and cache the history data"""
    return safe_api_call(f"{backend_url}/history")

# Helper function to generate consistent timestamps
def get_utc_timestamp():
    """Generate a UTC timestamp in a consistent format"""
    return datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")

def format_display_time(timestamp_str):
    try:
        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%H:%M:%S")
    except:
        return timestamp_str  # Return original if parsing fails

def get_current_time():
    """Get current time in HH:MM:SS format"""
    return datetime.now().strftime("%H:%M:%S")

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

    .pagination {
        display: flex;
        justify-content: center;
        margin-top: 15px;
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
    
    try:
        position = next((i for i, p in enumerate(queue) if p.get('name') == patient.get('name')), 0) + 1
        
        # Calculate wait time based on patients ahead in queue
        ahead_patients = queue[:position-1] if position > 0 else []
        wait_time = sum(base_times.get(p.get('severity', 3), 5) for p in ahead_patients)
        
        # Add base time for current patient
        wait_time += base_times.get(patient.get('severity', 3), 5)
        
        # Ensure minimum wait time
        return max(5, wait_time)
    except (TypeError, ValueError, IndexError):
        # Fallback for any errors in calculation
        return 10  # Default wait time

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
            # Clear caches when manually refreshing
            get_queue_data.clear()
            get_history_data.clear()
            st.rerun()
            
        if st.button("📊 Generate Report", key="report_btn"):
            history = get_history_data()
            
            if not history or "error" in history:
                st.error(f"Failed to fetch history: {history.get('error', 'Unknown error')}")
            elif not history:
                st.info("No patient data to generate report.")
            else:
                try:
                    report_data = [
                        {
                            "Name": p.get('name', 'Unknown'),
                            "Condition": p.get('condition', 'Not specified'),
                            "Severity": p.get('severity', 'N/A'),
                            "Timestamp": p.get('arrival_time', 'N/A'),
                            "Status": "Completed"
                        }
                        for p in history
                    ]
                    df = pd.DataFrame(report_data)
                    csv_data = df.to_csv(index=False).encode()
                    
                    st.download_button(
                        "⬇️ Download Patient Report (CSV)", 
                        csv_data, 
                        file_name=f"patient_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")

    # Patient history with pagination
    with st.expander("📜 Patient History", expanded=True):
        history = get_history_data()
        
        if not history or "error" in history:
            st.error(f"Failed to fetch history: {history.get('error', 'Unknown error')}")
        elif not history:
            st.info("No patient history yet.")
        else:
            # Implement pagination for history
            page_size = 10
            try:
                history_pages = [history[i:i + page_size] for i in range(0, len(history), page_size)]
                total_pages = len(history_pages)
                
                if total_pages > 0:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        current_page = st.number_input(
                            "Page", 
                            min_value=1, 
                            max_value=total_pages,
                            value=1,
                            key="history_page"
                        )
                    
                    # Display current page of history
                    display_history = history_pages[current_page-1]
                    for p in display_history:
                        st.markdown(f"""
                            <div class="history-item">
                                <div style="font-weight: bold;">{p.get('name', 'Unknown')}</div>
                                <div style="font-size: 0.85em; opacity: 0.9;">{p.get('condition', 'Not specified')}</div>
                                <span class="severity-badge severity-{p.get('severity', 3)}">Severity {p.get('severity', 3)}</span>
                                <div class="timestamp">Arrived: {format_display_time(p.get('arrival_time', 'N/A'))}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Pagination controls
                    st.markdown('<div class="pagination">', unsafe_allow_html=True)
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        if current_page > 1:
                            if st.button("← Previous", key="prev_history"):
                                st.session_state.history_page = current_page - 1
                                st.rerun()
                    with col3:
                        if current_page < total_pages:
                            if st.button("Next →", key="next_history"):
                                st.session_state.history_page = current_page + 1
                                st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.caption(f"Page {current_page} of {total_pages}")
            except Exception as e:
                st.error(f"Error displaying history: {str(e)}")

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
        current_time = datetime.utcnow()  # Use UTC consistently
        arrival_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        arrival_time_display = current_time.strftime("%H:%M:%S")
        st.markdown(f"""
            <div style="margin-top: 10px;">
                <div style="font-size: 0.9em; color: #64748b;">Arrival Time:</div>
                <div style="font-weight: bold;">{arrival_time_display}</div>
            </div>
        """, unsafe_allow_html=True)

    submitted = st.form_submit_button("🚑 Add to Queue", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        if not name or not condition:
            st.error("Please fill in all required fields")
        else:
            try:
                res = safe_api_call(
                    f"{backend_url}/add_patient",
                    method="post",
                    json_data={
                        "name": name,
                        "condition": condition,
                        "severity": severity,
                        "arrival_time": arrival_time
                    }
                )
                
                if res and "error" not in res:
                    st.success("✅ Patient successfully added to queue!")
                    # Clear the cache since we made changes
                    get_queue_data.clear()
                    get_history_data.clear()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Failed to add patient: {res.get('error', 'Unknown error')}")
            except Exception as e:
                st.error(f"❌ Error adding patient: {str(e)}")

# ─────────────────────────────────────────────
# Queue Display
# ─────────────────────────────────────────────
st.subheader("🧾 Current Triage Queue")
queue = get_queue_data()

if "error" in queue:
    st.error(f"Failed to fetch queue: {queue['error']}")
elif not queue:
    st.info("🎉 The queue is currently empty! No patients waiting.")
else:
    try:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.metric("Total Patients in Queue", len(queue))

        # Implementation of pagination for queue if needed
        page_size = 10  # Show 10 patients per page
        queue_pages = [queue[i:i + page_size] for i in range(0, len(queue), page_size)]
        total_pages = len(queue_pages)
        
        if total_pages > 0:
            if "queue_page" not in st.session_state:
                st.session_state.queue_page = 1
                
            if total_pages > 1:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    current_queue_page = st.number_input(
                        "Queue Page", 
                        min_value=1, 
                        max_value=total_pages,
                        value=st.session_state.queue_page,
                        key="queue_page_input"
                    )
                    st.session_state.queue_page = current_queue_page
            else:
                current_queue_page = 1
                
            # Display only current page of queue
            display_queue = queue_pages[current_queue_page-1]
            
            for i, p in enumerate(display_queue, start=(current_queue_page-1)*page_size + 1):
                emoji = "🚨" if p.get('severity') == 1 else "⚠️" if p.get('severity') == 2 else "✅"
                wait_time = calculate_wait_time(p, queue)
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"""
                        <div class="patient-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <strong style="font-size: 1.1em;">{emoji} {i}. {p.get('name', 'Unknown')}</strong>
                                    <div style="color: #64748b; font-size: 0.9em;">{p.get('condition', 'Not specified')}</div>
                                </div>
                                <span class="severity-badge severity-{p.get('severity', 3)}">Priority {p.get('severity', 3)}</span>
                            </div>
                            <div style="margin-top: 8px; display: flex; justify-content: space-between; align-items: center;">
                                <div style="font-size: 0.8em; color: #64748b;">
                                    Arrived: {format_display_time(p.get('arrival_time', 'N/A'))}
                                </div>
                                <div class="wait-time">
                                    Estimated wait: ~{wait_time} minutes
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("✅ Mark as Treated", key=f"treated_{i}"):
                        res = safe_api_call(
                            f"{backend_url}/mark_treated", 
                            method="post", 
                            json_data={"name": p.get('name')}
                        )
                        
                        if res and "error" not in res:
                            st.success(f"{p.get('name', 'Patient')} marked as treated.")
                            # Clear the cache since we made changes
                            get_queue_data.clear()
                            get_history_data.clear()
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Failed to update status: {res.get('error', 'Unknown error')}")
            
            # Pagination controls for queue if needed
            if total_pages > 1:
                st.markdown('<div class="pagination">', unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if current_queue_page > 1:
                        if st.button("← Previous", key="prev_queue"):
                            st.session_state.queue_page = current_queue_page - 1
                            st.rerun()
                with col3:
                    if current_queue_page < total_pages:
                        if st.button("Next →", key="next_queue"):
                            st.session_state.queue_page = current_queue_page + 1
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.caption(f"Queue Page {current_queue_page} of {total_pages}")
    except Exception as e:
        st.error(f"Error displaying queue: {str(e)}")

# ─────────────────────────────────────────────
# Call Next Patient
# ─────────────────────────────────────────────
st.subheader("📣 Call Next Patient")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔔 Call Next Patient", type="primary", key="next_patient_btn"):
        try:
            res = safe_api_call(f"{backend_url}/next_patient")
            
            if res and "error" not in res:
                next_p = res
                st.markdown(f"""
                    <div class="next-patient-banner">
                        <h3>Now Serving</h3>
                        <h2>{next_p.get('name', 'Unknown')}</h2>
                        <p>{next_p.get('condition', 'Not specified')} • Severity: {next_p.get('severity', 'N/A')}</p>
                        <div style="font-size: 0.9em; margin-top: 10px;">
                            Arrived at: {format_display_time(next_p.get('arrival_time', 'N/A'))}
                        </div>
                        <div style="font-size: 0.9em; margin-top: 5px;">
                            Called at: {get_current_time()}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Clear the cache since we may have changed the queue
                get_queue_data.clear()
                get_history_data.clear()
            else:
                st.warning(f"No patients in the queue to call. {res.get('error', '')}")
        except Exception as e:
            st.error(f"Error calling next patient: {str(e)}")
