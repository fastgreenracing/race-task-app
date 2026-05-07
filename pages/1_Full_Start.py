import streamlit as st
from google.cloud import firestore
import json

key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Site Coordinator | Full Start", layout="wide")

# --- COORDINATOR THEME ---
st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at top right, #2c2f33, #1a1c1e);
        background-attachment: fixed;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    .stApp::before {
        content: "";
        position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: radial-gradient(rgba(40, 167, 69, 0.05) 1px, transparent 1px);
        background-size: 40px 40px; pointer-events: none;
    }

    p, span, label, li { font-size: 16px !important; }
    h3 { font-size: 1.5rem !important; color: #28a745 !important; }

    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 15px;
        padding: 20px !important;
        background: rgba(255, 255, 255, 0.03);
    }
    
    [data-testid="stCheckbox"] { transform: scale(1.8); margin-left: 15px; }
    
    .status-header {
        padding: 40px;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

MILESTONES = ["Staff on Site", "Volunteers on Site", "Announcers on Site", "Timers on Site", "Set up of Start Line is Finished", "Full Marathon Start is 100%-awaiting Go Ahead"]

@st.fragment(run_every=2)
def render():
    st.title("📍 FULL START LOGISTICS")
    doc_ref = db.collection("site_statuses").document("full_start_FINAL")
    data = doc_ref.get().to_dict() or {}
    
    count = sum(1 for m in MILESTONES if data.get(m) == True)
    director_signal = data.get("director_signal", False)
    note_active = data.get("note_active", False)
    emergency = data.get("emergency_cancel", False)
    custom_note = data.get("custom_note", "")

    if emergency:
        st.markdown(f"<div class='status-header' style='background: #ff4b4b;'><h1 style='color:white !important;'>STOP: {custom_note}</h1></div>", unsafe_allow_html=True)
    elif director_signal:
        st.markdown("<div class='status-header' style='background: #28a745;'><h1 style='color:white !important;'>OKAY TO START ONTIME</h1></div>", unsafe_allow_html=True)
    elif note_active:
        st.markdown(f"<div class='status-header' style='background: #28a745;'><p style='font-size:14px; color:white !important;'>COMMAND NOTE:</p><h1 style='color:white !important;'>{custom_note}</h1></div>", unsafe_allow_html=True)
    elif count == 6:
        st.markdown("<div class='status-header' style='background: #ffc107;'><h1 style='color:white !important;'>PENDING APPROVAL</h1></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='status-header' style='background: #444444; border: 1px solid #666;'><h1 style='color:white !important;'>PREPARING ({count}/6)</h1></div>", unsafe_allow_html=True)

    st.divider()
    for m in MILESTONES:
        checked = data.get(m, False)
        col1, col2 = st.columns([1, 9])
        with col1:
            val = st.checkbox("", value=checked, key=f"m_{m}")
            if val != checked:
                doc_ref.set({m: val}, merge=True)
                if not val: doc_ref.update({"director_signal": False, "note_active": False})
                st.rerun()
        with col2: st.markdown(f"### {m}")

render()
