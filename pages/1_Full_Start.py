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

# --- PRECISION ALIGNMENT THEME ---
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
        font-family: "Times New Roman", Times, serif !important;
    }
    
    h1 {
        font-size: 24pt !important;
        font-family: "Times New Roman", Times, serif !important;
        font-weight: bold !important;
        color: #000000 !important;
    }

    /* Individual Milestone Grid Box */
    .milestone-grid {
        border: 1px solid #000000;
        border-radius: 2px;
        padding: 0px 15px !important;
        margin-bottom: 8px;
        display: flex;
        align-items: center; /* Vertical Center for everything */
        min-height: 65px;
        background-color: #FFFFFF;
        position: relative;
    }

    /* Milestone Text Styling */
    .milestone-text {
        font-size: 16pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
        font-weight: bold !important;
        margin-left: 50px; /* Space for the checkmark */
        display: flex;
        align-items: center;
        height: 65px; /* Matches grid min-height for centering */
    }

    /* Invisible clickable area */
    [data-testid="stCheckbox"] div[role="checkbox"] {
        opacity: 0 !important;
        width: 55px !important;
        height: 55px !important;
        cursor: pointer !important;
    }

    /* Large Floating Red Checkmark */
    [data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"]::after {
        content: '' !important;
        position: absolute;
        visibility: visible !important;
        opacity: 1 !important;
        left: 10px;
        top: 2px;
        width: 18px;
        height: 38px;
        border: solid #FF0000;
        border-width: 0 7px 7px 0;
        transform: rotate(45deg);
    }

    /* Cleanup Native Streamlit Elements */
    [data-testid="stCheckbox"] svg {
        display: none !important;
    }
    
    [data-testid="stCheckbox"] {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }

    .status-header {
        padding: 25px;
        border: 2px solid #000000;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 20px;
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

    # Checklist Rendering within Grids
    for m in MILESTONES:
        checked = data.get(m, False)
        
        st.markdown('<div class="milestone-grid">', unsafe_allow_html=True)
        col1, col2 = st.columns([0.05, 9.95]) # Tighter first column for flush checkmark
        with col1:
            val = st.checkbox("", value=checked, key=f"grid_{m}")
            if val != checked:
                doc_ref.set({m: val}, merge=True)
                if not val: 
                    doc_ref.update({"director_signal": False, "note_active": False})
                st.rerun()
        with col2:
            st.markdown(f'<div class="milestone-text">{m}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render()
