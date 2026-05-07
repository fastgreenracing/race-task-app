import streamlit as st
from google.cloud import firestore
import json
from datetime import datetime
import pytz

# 1. Database Connection
if "textkey" in st.secrets:
    key_dict = json.loads(st.secrets["textkey"])
    db = firestore.Client.from_service_account_info(key_dict)
else:
    st.error("Firestore secrets not found.")
    st.stop()

TIMEZONE = pytz.timezone("America/Los_Angeles")

st.set_page_config(page_title="Full Start Coordinator", layout="wide")

# --- BASELINE CSS ---
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
        font-family: "Times New Roman", Times, serif !important;
    }
    
    .milestone-label {
        font-size: 24pt !important;
        font-family: "Times New Roman", Times, serif !important;
        font-weight: bold !important;
        line-height: 1.1;
    }

    .timestamp-label {
        font-size: 12pt !important;
        color: #666666 !important;
        font-style: italic;
    }

    .note-timestamp {
        font-size: 14pt !important;
        display: block;
        margin-top: 8px;
        opacity: 0.9;
        font-weight: normal;
    }

    [data-testid="stCheckbox"] div[role="checkbox"] {
        width: 80px !important;
        height: 80px !important;
        cursor: pointer !important;
    }

    [data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"]::after {
        content: '' !important;
        position: absolute;
        visibility: visible !important;
        left: 25px; 
        top: 5px; 
        width: 25px; 
        height: 50px; 
        border: solid #FF0000;
        border-width: 0 10px 10px 0; 
        transform: rotate(45deg);
    }

    [data-testid="stCheckbox"] svg {
        display: none !important;
    }

    .status-header {
        padding: 25px;
        border: 2px solid #000000;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 20px;
        color: white;
    }

    hr {
        margin: 1.2em 0 !important;
        border: 0;
        border-top: 2px solid #EEEEEE;
    }
    </style>
    """, unsafe_allow_html=True)

MILESTONES = [
    "Staff on Site",
    "Volunteers on Site",
    "Announcers on Site",
    "Timers on Site",
    "Set up of Start Line is Finished",
    "Full Marathon Start is 100%-awaiting Go Ahead"
]

@st.fragment(run_every=2)
def render():
    st.title("Full Marathon Start Checklist")
    
    doc_ref = db.collection("site_statuses").document("full_start_FINAL")
    data = doc_ref.get().to_dict() or {}
    
    count = sum(1 for m in MILESTONES if data.get(m) == True)
    director_signal = data.get("director_signal", False)
    note_active = data.get("note_active", False)
    emergency = data.get("emergency_cancel", False)
    note_ts = data.get("note_timestamp", "")

    # --- STATUS HEADER LOGIC ---
    if emergency:
        st.markdown("<div class='status-header' style='background:#FF0000;'><h1>🛑 EMERGENCY STOP</h1></div>", unsafe_allow_html=True)
    
    # 1. FINAL GO-AHEAD (Director Signal or Active Note)
    elif director_signal or note_active: 
        msg = data.get("custom_note", "Okay to start ontime") if (note_active and data.get("custom_note")) else "Okay to start ontime"
        ts_html = f"<div class='note-timestamp'>Signal Received: {note_ts}</div>" if note_ts else ""
        st.markdown(f"<div class='status-header' style='background:#008000;'><h1>🚀 {msg}{ts_html}</h1></div>", unsafe_allow_html=True)
    
    # 2. SITE LEAD READY (All milestones checked, waiting for Director)
    elif count == len(MILESTONES):
        st.markdown("<div class='status-header' style='background:#FFD700; color:black;'><h1>⏳ WAITING FOR DIRECTOR</h1></div>", unsafe_allow_html=True)
    
    # 3. IN PROGRESS
    else:
        st.markdown(f"<div class='status-header' style='background:#EEEEEE; color:black;'><h1>PREPARING ({count}/{len(MILESTONES)})</h1></div>", unsafe_allow_html=True)

    st.divider()

    # --- MILESTONE LIST ---
    for i, m in enumerate(MILESTONES):
        checked = data.get(m, False)
        ts_key = f"{m}_ts"
        timestamp_str = data.get(ts_key, "")
        
        col_check, col_text = st.columns([0.15, 9.85])
        
        with col_check:
            val = st.checkbox("", value=checked, key=f"baseline_v3_{m}")
            if val != checked:
                now = datetime.now(TIMEZONE)
                current_ts = now.strftime("%I:%M:%S %p")
                
                update_payload = {m: val, ts_key: current_ts if val else ""}
                doc_ref.set(update_payload, merge=True)
                
                # Log action to Firestore
                db.collection("milestone_logs").add({
                    "milestone": m,
                    "action": "Completed" if val else "Unchecked",
                    "timestamp": now,
                    "display_time": current_ts,
                    "event_id": "full_start_FINAL"
                })

                # Safety: If Site Lead unchecks a milestone, kill the Green light
                if not val: 
                    doc_ref.update({"director_signal": False, "note_active": False})
                st.rerun()
        
        with col_text:
            st.markdown(f'<div class="milestone-label">{m}</div>', unsafe_allow_html=True)
            if checked and timestamp_str:
                st.markdown(f'<div class="timestamp-label">Completed at {timestamp_str}</div>', unsafe_allow_html=True)
        
        if i < len(MILESTONES) - 1:
            st.markdown("---")

if __name__ == "__main__":
    render()
    
