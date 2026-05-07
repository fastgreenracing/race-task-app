import streamlit as st
from google.cloud import firestore
import json

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Full Start Coordinator", layout="wide")

# --- CLEAN WHITE THEME WITH CUSTOM "X" CHECKBOXES ---
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
        font-family: "Times New Roman", Times, serif !important;
    }
    
    p, span, label, li {
        font-size: 16pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
    }

    h1, h2 {
        font-size: 24pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* Milestone Container */
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 1px solid #000000 !important;
        border-radius: 4px;
        padding: 8px 15px !important;
        margin-bottom: 6px !important;
        background: #FDFDFD;
    }
    
    /* Hide the default browser checkmark and replace with an X */
    [data-testid="stCheckbox"] input[type="checkbox"]:checked ~ div span::after {
        content: "X" !important;
        font-family: Arial, sans-serif !important; /* Use a clean font for the X */
        font-weight: bold !important;
        font-size: 22px !important; /* Adjust size to fill box */
        color: #000000 !important;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        visibility: visible !important;
    }

    /* Hide the actual check icon svg */
    [data-testid="stCheckbox"] svg {
        display: none !important;
    }

    /* Ensure the box itself stays visible */
    [data-testid="stCheckbox"] div[role="checkbox"] {
        background-color: #FFFFFF !important;
        border: 2px solid #000000 !important;
        border-radius: 2px !important;
        width: 25px !important;
        height: 25px !important;
    }
    
    .status-header {
        padding: 30px;
        border: 2px solid #000000;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

MILESTONES = ["Staff on Site", "Volunteers on Site", "Announcers on Site", "Timers on Site", "Set up of Start Line is Finished", "Full Marathon Start is 100%-awaiting Go Ahead"]

@st.fragment(run_every=2)
def render():
    st.title("Full Marathon Start: Logistics Checklist")
    doc_ref = db.collection("site_statuses").document("full_start_FINAL")
    data = doc_ref.get().to_dict() or {}
    
    count = sum(1 for m in MILESTONES if data.get(m) == True)
    director_signal = data.get("director_signal", False)
    note_active = data.get("note_active", False)
    emergency = data.get("emergency_cancel", False)
    custom_note = data.get("custom_note", "")

    if emergency:
        st.markdown(f"<div class='status-header' style='background: #FF0000;'><h1 style='color:white !important;'>STOP: {custom_note}</h1></div>", unsafe_allow_html=True)
    elif director_signal:
        st.markdown("<div class='status-header' style='background: #008000;'><h1 style='color:white !important;'>Okay to start ontime</h1></div>", unsafe_allow_html=True)
    elif note_active:
        st.markdown(f"<div class='status-header' style='background: #008000;'><p style='color:white !important; font-size: 16pt;'>DIRECTOR NOTE:</p><h1 style='color:white !important;'>{custom_note}</h1></div>", unsafe_allow_html=True)
    elif count == 6:
        st.markdown("<div class='status-header' style='background: #FFD700;'><h1 style='color:black !important;'>WAITING FOR DIRECTOR</h1></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='status-header' style='background: #EEEEEE;'><h1 style='color:black !important;'>PREPARING ({count}/6)</h1></div>", unsafe_allow_html=True)

    st.divider()
    for m in MILESTONES:
        checked = data.get(m, False)
        col1, col2 = st.columns([0.5, 9.5])
        with col1:
            val = st.checkbox("", value=checked, key=f"m_{m}")
            if val != checked:
                doc_ref.set({m: val}, merge=True)
                if not val: doc_ref.update({"director_signal": False, "note_active": False})
                st.rerun()
        with col2:
            st.markdown(f"**{m}**")

render()
