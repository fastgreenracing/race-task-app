import streamlit as st
from google.cloud import firestore
import json

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Full Start Coordinator", layout="wide")

# --- CLEAN WHITE THEME: CENTERED & BORDERLESS CHECKBOXES ---
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

    /* Milestone Container Box */
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 1px solid #000000 !important;
        border-radius: 2px;
        padding: 8px 10px !important;
        margin-bottom: 4px !important;
        background: #FFFFFF;
        display: flex;
        align-items: center; /* Vertically centers the contents */
    }
    
    /* Remove the box around the checkmark itself */
    [data-testid="stCheckbox"] div[role="checkbox"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    /* Scale and position the checkmark */
    [data-testid="stCheckbox"] { 
        transform: scale(2.0); 
        margin-left: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    /* Hide the standard checkbox background when unchecked to keep it "borderless" */
    [data-testid="stCheckbox"] div[data-testid="stWidgetLabel"] {
        display: none;
    }
    
    .status-header {
        padding: 25px;
        border: 2px solid #000000;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

MILESTONES = ["Staff on Site", "Volunteers on Site", "Announcers on Site", "Timers on Site", "Set up of Start Line is Finished", "Full Marathon Start is 100%-awaiting Go Ahead"]

@st.fragment(run_every=2)
def render():
    st.title("Full Marathon Start Checklist")
    doc_ref = db.collection("site_statuses").document("full_start_FINAL")
    data = doc_ref.get().to_dict() or {}
    
    count = sum(1 for m in MILESTONES if data.get(m) == True)
    director_signal = data.get("director_signal", False)
    note_active = data.get("note_active", False)
    emergency = data.get("emergency_cancel", False)
    custom_note = data.get("custom_note", "")

    # Status Display Headers
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
        # Using columns to help with the side-by-side centering
        col1, col2 = st.columns([0.4, 9.6])
        with col1:
            val = st.checkbox("", value=checked, key=f"m_{m}")
            if val != checked:
                doc_ref.set({m: val}, merge=True)
                if not val: doc_ref.update({"director_signal": False, "note_active": False})
                st.rerun()
        with col2:
            # Inline text with vertical padding to match the checkbox scale
            st.markdown(f"<div style='padding-top:10px;'><b>{m}</b></div>", unsafe_allow_html=True)

render()
