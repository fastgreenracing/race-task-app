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

# --- DATABASE REFERENCE ---
doc_ref = db.collection("site_statuses").document("full_start_FINAL")
data = doc_ref.get().to_dict() or {}

# --- MILESTONE TRACKING LOGIC ---
MILESTONES = [
    "Staff on Site",
    "Volunteers on Site",
    "Announcers on Site",
    "Timers on Site",
    "Set up of Start Line is Finished",
    "Full Marathon Start is 100%-awaiting Go Ahead"
]

count = sum(1 for m in MILESTONES if data.get(m) == True)

# --- 1. LIVE PROGRESS MONITOR ---
st.header("Ground Operations Progress")
progress_pct = count / len(MILESTONES)
st.progress(progress_pct)

if count == len(MILESTONES):
    st.warning("⚠️ ALL MILESTONES COMPLETE: Site Lead is awaiting your Go Ahead.")
else:
    st.info(f"Status: {count} of {len(MILESTONES)} milestones completed.")

# Show which specific milestones are done
with st.expander("View Milestone Details"):
    for m in MILESTONES:
        is_done = data.get(m, False)
        ts = data.get(f"{m}_ts", "")
        status_char = "✅" if is_done else "⬜"
        st.write(f"{status_char} **{m}** {f'({ts})' if ts else ''}")

st.divider()

# --- 2. DIRECTOR CONTROL PANEL ---
st.header("Start Line Communications")

with st.container(border=True):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        custom_msg = st.text_input("Custom Instruction / Note", placeholder="e.g., Hold start 5 mins for shuttle")
    
    with col2:
        st.write("### Actions")
        send_btn = st.button("🚀 Send Note & Go", use_container_width=True)
        clear_btn = st.button("🧹 Clear All Signals", use_container_width=True)

# --- SEND LOGIC ---
if send_btn:
    now_ts = datetime.now(TIMEZONE).strftime("%I:%M:%S %p")
    doc_ref.update({
        "custom_note": custom_msg if custom_msg else "Okay to start ontime",
        "note_active": True,
        "director_signal": True,
        "note_timestamp": now_ts
    })
    st.success(f"Signal sent at {now_ts}")
    st.rerun()

# --- CLEAR LOGIC ---
if clear_btn:
    doc_ref.update({
        "note_active": False,
        "director_signal": False,
        "custom_note": "",
        "note_timestamp": "",
        "emergency_cancel": False
    })
    # Optional: Also clear milestones if you want a total reset
    # for m in MILESTONES: doc_ref.update({m: False, f"{m}_ts": ""})
    st.warning("All signals cleared.")
    st.rerun()

st.divider()

# --- 3. LIVE BROADCAST PREVIEW ---
st.subheader("Current Broadcast Status")
if data.get("emergency_cancel"):
    st.error("🛑 EMERGENCY STOP ACTIVE")
elif data.get("note_active") or data.get("director_signal"):
    msg = data.get('custom_note', 'Okay to start ontime')
    st.success(f"🟢 GREEN LIGHT: {msg} (Sent: {data.get('note_timestamp')})")
else:
    st.info("⚪ System Ready. Awaiting ground completion.")
