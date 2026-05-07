import streamlit as st
from google.cloud import firestore
import json

key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Site Lead | Full Start", layout="wide")

# --- SLEEK SITE LEAD CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #28a745; }
    h1, h2, h3, p, label { color: #28a745 !important; }
    
    /* Modern Checkbox Container */
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 1px solid rgba(40, 167, 69, 0.2) !important;
        border-radius: 20px;
        padding: 30px !important;
        margin-bottom: 20px !important;
        background-color: #050505;
        transition: transform 0.2s;
    }
    [data-testid="stCheckbox"] { transform: scale(2.2); margin-left: 20px; }
    
    .header-box {
        padding: 40px;
        border-radius: 25px;
        text-align: center;
        margin-bottom: 40px;
        box-shadow: 0 15px 40px rgba(0,0,0,0.6);
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

    # PROFESSIONAL COLOR-CODED HEADER
    if emergency:
        st.markdown(f"<div class='header-box' style='background:#ff4b4b; border: 4px solid white;'><h1 style='color:white !important; font-size:3rem;'>🛑 EMERGENCY CANCELLATION</h1><p style='color:white !important;'>{custom_note}</p></div>", unsafe_allow_html=True)
    elif director_signal:
        # GREEN: Approved
        st.markdown("<div class='header-box' style='background:#1b5e20; border: 4px solid #28a745;'><h1 style='color:white !important; font-size:3rem;'>🚀 OKAY TO START ONTIME</h1></div>", unsafe_allow_html=True)
    elif note_active:
        # GREEN: Approved with Note
        st.markdown(f"<div class='header-box' style='background:#1b5e20; border: 4px solid #28a745;'><p style='color:white !important; font-size:1.2rem; opacity:0.8;'>DIRECTOR INSTRUCTION:</p><h1 style='color:white !important; font-size:2.8rem;'>⚡ {custom_note}</h1></div>", unsafe_allow_html=True)
    elif count == 6:
        # YELLOW: Ready, waiting for Director
        st.markdown("<div class='header-box' style='background:#5a4100; border: 4px solid #ffc107;'><h1 style='color:white !important; font-size:3rem;'>⏳ AWAITING DIRECTOR APPROVAL</h1><p style='color:white !important;'>Milestones 100% Complete</p></div>", unsafe_allow_html=True)
    else:
        # RED: Still working
        st.markdown(f"<div class='header-box' style='background:#4c0000; border: 2px solid #ff4b4b;'><h1 style='color:white !important; font-size:3rem;'>NO GO</h1><p style='color:white !important;'>{count} of 6 Milestones Cleared</p></div>", unsafe_allow_html=True)

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
