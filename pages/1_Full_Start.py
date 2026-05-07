import streamlit as st
from google.cloud import firestore
import json

key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Site Coordinator | Full Start", layout="wide")

# --- SLEEK COORDINATOR CSS ---
st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at top right, #1a1c1e, #0f1011);
        background-attachment: fixed;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Technical Grid Overlay */
    .stApp::before {
        content: "";
        position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: radial-gradient(rgba(40, 167, 69, 0.05) 1px, transparent 1px);
        background-size: 40px 40px; pointer-events: none;
    }

    /* Glassmorphism Checkbox Containers */
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 20px;
        padding: 25px !important;
        margin-bottom: 18px !important;
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(10px);
    }
    
    [data-testid="stCheckbox"] { transform: scale(2.0); margin-left: 20px; }
    
    .status-header {
        padding: 45px;
        border-radius: 28px;
        text-align: center;
        margin-bottom: 35px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    }
    </style>
    """, unsafe_allow_html=True)

MILESTONES = ["Staff on Site", "Volunteers on Site", "Announcers on Site", "Timers on Site", "Set up of Start Line is Finished", "Full Marathon Start is 100%-awaiting Go Ahead"]

@st.fragment(run_every=2)
def render():
    doc_ref = db.collection("site_statuses").document("full_start_FINAL")
    data = doc_ref.get().to_dict() or {}
    
    count = sum(1 for m in MILESTONES if data.get(m) == True)
    director_signal = data.get("director_signal", False)
    note_active = data.get("note_active", False)
    emergency = data.get("emergency_cancel", False)
    custom_note = data.get("custom_note", "")

    # SOPHISTICATED COLOR-CODED HEADERS
    if emergency:
        st.markdown(f"<div class='status-header' style='background: linear-gradient(135deg, #8b0000, #ff4b4b); border: 2px solid white;'><h1 style='color:white !important; font-size:3.2rem;'>EMERGENCY STOP</h1><p style='color:white !important; font-weight: 600;'>{custom_note}</p></div>", unsafe_allow_html=True)
    elif director_signal:
        st.markdown("<div class='status-header' style='background: linear-gradient(135deg, #0d4d1e, #28a745); border: 1px solid rgba(255,255,255,0.2);'><h1 style='color:white !important; font-size:3.2rem;'>OKAY TO START ONTIME</h1><p style='color:white !important; opacity:0.8;'>Signal Verified by Command</p></div>", unsafe_allow_html=True)
    elif note_active:
        st.markdown(f"<div class='status-header' style='background: linear-gradient(135deg, #0d4d1e, #28a745); border: 1px solid rgba(255,255,255,0.2);'><p style='color:white !important; font-size:1rem; letter-spacing:2px; font-weight:800;'>COMMAND INSTRUCTION:</p><h1 style='color:white !important; font-size:2.8rem;'>⚡ {custom_note}</h1></div>", unsafe_allow_html=True)
    elif count == 6:
        st.markdown("<div class='status-header' style='background: linear-gradient(135deg, #6b5500, #ffc107); border: 1px solid rgba(255,255,255,0.1);'><h1 style='color:white !important; font-size:3.2rem;'>PENDING APPROVAL</h1><p style='color:white !important;'>Waiting for Director Clearance</p></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='status-header' style='background: linear-gradient(135deg, #3a0000, #660000); border: 1px solid rgba(255,255,255,0.05);'><h1 style='color:white !important; font-size:3.2rem;'>PREPARING</h1><p style='color:white !important;'>{count} of 6 Pre-Race Milestones Cleared</p></div>", unsafe_allow_html=True)

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
