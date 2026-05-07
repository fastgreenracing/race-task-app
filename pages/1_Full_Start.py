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

# --- THE "ZERO-GAP" JUMBO THEME ---
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
    }

    /* Milestone Row: Acts like a table row to force bottom alignment */
    .milestone-row {
        display: table;
        width: 100%;
        border-bottom: 4px solid #000000; /* Extra thick border */
        margin: 0 !important;
        padding: 0 !important;
        background-color: transparent;
    }

    /* Milestone Text: Anchored to the very bottom */
    .milestone-text {
        display: table-cell;
        vertical-align: center;
        font-size: 24pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
        font-weight: bold !important;
        padding-bottom: 60px !important; /* Minimal buffer from line */
        padding-top: 45px !important;   /* Large top padding for height */
        line-height: 1.0 !important;
    }

    /* Checkbox Container: Also anchored to bottom */
    .check-container {
        display: table-cell;
        vertical-align: bottom;
        width: 120px;
        padding-bottom: 0px !important;
    }

    /* Invisible clickable area: Large hit zone */
    [data-testid="stCheckbox"] div[role="checkbox"] {
        opacity: 0 !important;
        width: 100px !important;
        height: 100px !important;
        cursor: pointer !important;
    }

    /* DOUBLE SCALE RED CHECKMARK (100% Increase) */
    [data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"]::after {
        content: '' !important;
        position: absolute;
        visibility: visible !important;
        opacity: 1 !important;
        left: 10px; 
        top: -65px; /* Adjusted to keep the massive check level with jumbo text */
        width: 40px; 
        height: 85px; 
        border: solid #FF0000;
        border-width: 0 18px 18px 0; /* Massive thickness */
        transform: rotate(45deg);
    }

    /* Remove Streamlit default spacing */
    [data-testid="stCheckbox"] {
        margin: 0 !important;
        padding: 0 !important;
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
        
        # New Table-Row approach to force bottom alignment
        st.markdown(f'''
            <div class="milestone-row">
                <div class="check-container" id="check_{m}"></div>
                <div class="milestone-text">{m}</div>
            </div>
        ''', unsafe_allow_html=True)
        
        # Inject the actual checkbox into the container
        # Note: Streamlit widgets usually render in order, 
        # so we keep the columns for functional logic but hide the gap
        col1, col2 = st.columns([0.1, 9.9])
        with col1:
            # Shift the widget up into the table row space using a negative margin
            st.markdown('<div style="margin-top:-60px;">', unsafe_allow_html=True)
            val = st.checkbox("", value=checked, key=f"final_jumbo_{m}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if val != checked:
                doc_ref.set({m: val}, merge=True)
                if not val: 
                    doc_ref.update({"director_signal": False, "note_active": False})
                st.rerun()

if __name__ == "__main__":
    render()
