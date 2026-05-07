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

st.set_page_config(page_title="Race Director Dashboard", layout="wide")

st.title("🏃‍♂️ Race Director Command Center")

# --- DIRECTOR CONTROL PANEL ---
st.header("Start Line Communications")

# Create a container for the controls
with st.container(border=True):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        custom_msg = st.text_input("Custom Instruction / Note", placeholder="e.g., Hold start 5 mins for shuttle")
    
    with col2:
        st.write("### Actions")
        send_btn = st.button("🚀 Send Note & Go", use_container_width=True)
        clear_btn = st.button("🧹 Clear All Signals", use_container_width=True)

# 2. Logic for Sending Notes
doc_ref = db.collection("site_statuses").document("full_start_FINAL")

if send_btn:
    now_ts = datetime.now(TIMEZONE).strftime("%I:%M:%S %p")
    # Update Firestore with the note and the current timestamp
    doc_ref.update({
        "custom_note": custom_msg if custom_msg else "Okay to start ontime",
        "note_active": True,
        "director_signal": True,
        "note_timestamp": now_ts
    })
    st.success(f"Signal sent at {now_ts}")

if clear_btn:
    doc_ref.update({
        "note_active": False,
        "director_signal": False,
        "custom_note": "",
        "note_timestamp": "",
        "emergency_cancel": False
    })
    st.warning("All signals cleared.")

st.divider()

# --- OPTIONAL: GLOBAL STATUS PREVIEW ---
st.subheader("Current Start Line Status")
data = doc_ref.get().to_dict() or {}

if data.get("emergency_cancel"):
    st.error("🛑 EMERGENCY STOP ACTIVE")
elif data.get("note_active") or data.get("director_signal"):
    st.success(f"🟢 SIGNAL ACTIVE: {data.get('custom_note')} (Sent: {data.get('note_timestamp')})")
else:
    st.info("⚪ No active signals.")
