import streamlit as st
from google.cloud import firestore
import json

# 1. Database Connection
if "textkey" in st.secrets:
    key_dict = json.loads(st.secrets["textkey"])
    db = firestore.Client.from_service_account_info(key_dict)
else:
    st.error("Firestore secrets not found.")
    st.stop()

st.set_page_config(page_title="Full Start Coordinator", layout="wide")

# --- THE "FLUSH-LEFT" RED CHECK THEME ---
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
        font-family: "Times New Roman", Times, serif !important;
    }
    
    p, span, label, b, .stMarkdown {
        font-size: 16pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
    }

    h1 {
        font-size: 24pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* 1. THE MAIN MILESTONE CONTAINER */
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 1px solid #000000 !important;
        border-radius: 2px;
        padding: 0px 10px !important;
        margin-bottom: 5px !important;
        background: #FFFFFF;
        display: flex;
        align-items: center; 
        min-height: 65px; /* Fixed height for consistent alignment */
        overflow: visible !important;
    }
    
    /* 2. MAKE THE NATIVE BOX INVISIBLE BUT LARGE ENOUGH TO CLICK */
    [data-testid="stCheckbox"] div[role="checkbox"] {
        opacity: 0 !important; 
        width: 60px !important;
        height: 60px !important;
        cursor: pointer !important;
    }

    /* 3. BOLD RED CHECKMARK - Sized to fill the 'purple box' area */
    [data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"]::after {
        content: '' !important;
        position: absolute;
        visibility: visible !important;
        opacity: 1 !important;
        left: 10px;   /* Anchored left */
        top: 2px;    /* Centered vertically in the row */
        width: 22px; /* Wide footprint */
        height: 42px; /* Tall footprint */
        border: solid #FF4B4B; /* Streamlit Red / Race Red */
        border-width: 0 8px 8px 0; /* Thick lines to fill the space */
        transform: rotate(45deg);
    }

    /* 4. HIDE NATIVE OVERLAYS */
    [data-testid="stCheckbox"] svg {
        display: none !important;
    }
    [data-testid="stCheckbox"] div[data-testid="stWidgetLabel"] div {
        border: none !important;
        background: transparent !important;
    }

    .status-header {
        padding: 25px;
        border: 2px solid #000000;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
        color: white;
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

    if emergency:
        st.markdown("<div class='status-header' style='background:#FF0000;'><h1>🛑 EMERGENCY STOP</h1></div>", unsafe_allow_html=True)
    elif director_signal or note_active: 
        msg = data.get("custom_note", "Okay to start ontime") if note_active else "Okay to start ontime"
        st.markdown(f"<div class='status-header' style='background:#008000;'><h1>🚀 {msg}</h1></div>", unsafe_allow_html=True)
    elif count == 6:
        st.markdown("<div class='status-header' style='background:#FFD700; color:black;'><h1>⏳ WAITING FOR DIRECTOR</h1></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='status-header' style='background:#EEEEEE; color:black;'><h1>PREPARING ({count}/6)</h1></div>", unsafe_allow_html=True)

    st.divider()

    for m in MILESTONES:
        checked = data.get(m, False)
        # Ratio ensures col1 is just for the checkmark, col2 is for text
        col1, col2 = st.columns([0.1, 9.9]) 
        with col1:
            val = st.checkbox("", value=checked, key=f"m_{m}")
            if val != checked:
                doc_ref.set({m: val}, merge=True)
                if not val: 
                    doc_ref.update({"director_signal": False, "note_active": False})
                st.rerun()
        with col2:
            # margin-left:60px provides the gap so the text and checkmark are aligned but distinct
            st.markdown(f"<div style='margin-left:60px; padding-top:18px;'><b>{m}</b></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    render()
